# P2P Payment Entity Resolution - Domain Specification

## Domain Overview

**Industry**: Peer-to-Peer Payment Systems  
**Primary Use Case**: User entity resolution for fraud detection and prevention  
**Key Objective**: Link user accounts across devices, IPs, and transactions to detect:
- Multi-accounting fraud
- Account takeover
- Payment fraud rings
- Identity theft
- Money mule networks

---

## Entity Types

### 1. User Accounts
The primary entity being resolved. Multiple user accounts may represent the same real-world individual.

**Attributes**:
- Identity: user_id, email, phone, name, DOB
- Verification: KYC status, verified bank accounts, document verification
- Behavior: transaction patterns, login patterns, recipient networks
- Trust: account age, source trust score, fraud history

**Resolution Goal**: Determine if multiple user accounts belong to the same person

---

### 2. Payment Devices
Devices used for payment transactions (mobile apps, web browsers)

**Attributes**:
- Technical: device_id, fingerprint, OS, app version, screen resolution
- Location: timezone, language, IP address
- Behavior: usage patterns, transaction frequency

**Linking Signal**: Shared devices indicate potential entity linkage (or device sharing)

---

### 3. IP Addresses
Network identifiers associated with payment sessions

**Attributes**:
- Identity: IP address, ISP provider, geolocation
- Risk: VPN/proxy flag, reputation score, blacklist status
- Temporal: first seen, last seen, usage frequency

**Linking Signal**: Shared IPs indicate potential entity linkage (with caution for shared networks)

---

### 4. Transactions
Payment events connecting entities

**Attributes**:
- Core: amount, currency, timestamp, status
- Participants: sender_id, receiver_id
- Metadata: payment method, reversal flag, dispute flag
- Risk: fraud score, velocity metrics

**Analytical Signal**: Transaction graphs reveal entity relationships and fraud patterns

---

## P2P Payment-Specific Constraints

### Hard Constraints (Edge Removal)

#### 1. ✋ Conflicting Verified Identity

**Purpose**: Prevent merging users with different verified KYC identities

**Logic**:
```python
if (user_a.kyc_verified and user_b.kyc_verified):
    if (user_a.kyc_name != user_b.kyc_name or
        user_a.kyc_dob != user_b.kyc_dob or
        user_a.kyc_ssn != user_b.kyc_ssn):
        # These are definitively different people
        REMOVE_EDGE
```

**Fraud Scenario Prevented**:
- Legitimate user incorrectly linked to fraudster with stolen KYC
- Different individuals sharing same device/IP (roommates, family)

**Example**:
```
User A: John Smith, DOB: 1990-05-15, SSN: ***-**-1234 [KYC Verified]
User B: Jane Doe, DOB: 1985-03-22, SSN: ***-**-5678 [KYC Verified]
Shared IP: 192.168.1.100 (coffee shop WiFi)

→ HARD CONSTRAINT PREVENTS MERGE despite shared IP
```

---

#### 2. ✋ Conflicting Bank Ownership

**Purpose**: Users with different verified bank accounts are different entities

**Logic**:
```python
if (user_a.verified_bank_owner != user_b.verified_bank_owner):
    # Bank accounts verified via micro-deposits or Plaid
    REMOVE_EDGE
```

**Fraud Scenario Prevented**:
- Account takeover where fraudster adds their own bank account
- Money mule using victim's payment account

**Example**:
```
User A: Bank account owner = "John A Smith"
User B: Bank account owner = "Robert Johnson"
Shared device fingerprint: ABC123XYZ (potential device reuse)

→ HARD CONSTRAINT PREVENTS MERGE - different bank owners
```

---

#### 3. ✋ Impossible Geolocation

**Purpose**: Cannot be in two distant locations within physically impossible timeframe

**Logic**:
```python
distance_km = haversine(user_a.location, user_b.location)
time_diff_hours = abs(user_a.timestamp - user_b.timestamp).hours

if distance_km > 500 and time_diff_hours < 1:
    # Impossible to travel 500+ km in under 1 hour
    REMOVE_EDGE
```

**Fraud Scenario Prevented**:
- Account takeover from different geographic location
- Stolen credentials used by attacker in different country

**Example**:
```
User A: Login from New York, USA at 10:00 AM EST
User B: Login from London, UK at 10:30 AM EST (3:30 PM GMT)
Distance: ~5,500 km, Time difference: 30 minutes

→ HARD CONSTRAINT PREVENTS MERGE - impossible travel
```

---

#### 4. ✋ Conflicting Device OS Families

**Purpose**: User cannot use iOS and Android simultaneously with different accounts

**Logic**:
```python
if (user_a.device_os in ['iOS', 'iPadOS'] and 
    user_b.device_os == 'Android' and
    abs(user_a.timestamp - user_b.timestamp) < 24h):
    # Unlikely to switch OS families rapidly for same person
    REMOVE_EDGE
```

**Fraud Scenario Prevented**:
- Multi-accounting using different devices
- Shared device pools in fraud farms

**Example**:
```
User A: iPhone 13 (iOS 16.1) - Transaction at 2:00 PM
User B: Samsung Galaxy (Android 12) - Transaction at 2:15 PM
Shared email domain: @gmail.com (common domain, weak signal)

→ HARD CONSTRAINT PREVENTS MERGE - different OS families too close in time
```

---

#### 5. ✋ Fraud Contamination

**Purpose**: Legitimate users cannot be merged with confirmed fraud accounts

**Logic**:
```python
if ((user_a.fraud_confirmed and not user_b.fraud_confirmed) or
    (user_b.fraud_confirmed and not user_a.fraud_confirmed)):
    # Don't contaminate clean accounts with fraud labels
    REMOVE_EDGE
```

**Fraud Scenario Prevented**:
- False positives that would incorrectly flag legitimate users
- Fraudster using stolen device/credentials temporarily

**Example**:
```
User A: Confirmed fraud (chargeback fraud, account closed)
User B: Legitimate user with 2-year good standing
Shared IP (one-time): 203.0.113.45 (public WiFi)

→ HARD CONSTRAINT PREVENTS MERGE - protect legitimate user from fraud label
```

---

### Soft Constraints (Edge Penalization)

#### 1. ⚠️ Low Source Trust

**Purpose**: Reduce confidence when data sources are unreliable

**Penalty**: 30% edge weight reduction

**Logic**:
```python
if (user_a.source_trust_score < 0.5 or user_b.source_trust_score < 0.5):
    edge_weight *= 0.7  # 30% penalty
```

**Scenarios**:
- Data from user-submitted forms (easy to fake)
- Legacy data with known quality issues
- Third-party enrichment data with low accuracy

---

#### 2. ⚠️ Account Age Mismatch

**Purpose**: Linking very new accounts to very old accounts is suspicious

**Penalty**: 25% edge weight reduction

**Logic**:
```python
age_diff_days = abs(user_a.account_age_days - user_b.account_age_days)
if age_diff_days > 365:
    edge_weight *= 0.75  # 25% penalty
```

**Fraud Scenarios**:
- Fraudster creates new account after old one banned
- Account takeover of long-standing account

---

#### 3. ⚠️ VPN/Proxy Usage

**Purpose**: VPN obscures true location and identity signals

**Penalty**: 20% edge weight reduction

**Logic**:
```python
if (user_a.vpn_detected or user_b.vpn_detected):
    edge_weight *= 0.8  # 20% penalty
```

**Fraud Scenarios**:
- Fraudster hiding true location
- Legitimate privacy-conscious user (acceptable false positive trade-off)

---

#### 4. ⚠️ Behavioral Mismatch

**Purpose**: Very different transaction behaviors suggest different users

**Penalty**: 30% edge weight reduction

**Logic**:
```python
amount_diff = abs(user_a.avg_transaction - user_b.avg_transaction)
if (amount_diff > $1000 or 
    user_a.transaction_frequency != user_b.transaction_frequency):
    edge_weight *= 0.7  # 30% penalty
```

**Scenarios**:
- High-value merchant vs. personal user on same IP (shared office)
- Fraudster with different behavior pattern than victim

---

#### 5. ⚠️ Low IP Reputation

**Purpose**: IPs with poor reputation reduce linking confidence

**Penalty**: 35% edge weight reduction

**Logic**:
```python
if (user_a.ip_reputation < 0.3 or user_b.ip_reputation < 0.3):
    edge_weight *= 0.65  # 35% penalty
```

**Fraud Scenarios**:
- Known fraud IP ranges (VPS, hosting providers used for automation)
- Compromised residential IPs (botnets)

---

## Fraud Pattern Detection via Entity Resolution

### Pattern 1: Multi-Accounting (Promo Abuse)

**Description**: Single user creates multiple accounts to exploit referral bonuses, promotions

**Graph Signature**:
```
User A ----[same device]---- User B
  |                             |
  [same IP]                [same IP]
  |                             |
User C ----[same name]------ User D

All accounts created within 1 week
All claimed $10 signup bonus
```

**Detection via ER**:
- High-confidence entity cluster linking A, B, C, D
- Shared device fingerprints
- Similar transaction patterns (immediate cash-out after bonus)

**Entity Resolution Output**:
```json
{
  "entity_id": "FRAUD_MULTI_001",
  "accounts": ["A", "B", "C", "D"],
  "confidence": 0.92,
  "fraud_pattern": "multi_accounting",
  "evidence": [
    "Shared device fingerprint across all accounts",
    "Same IP address for registration",
    "Similar names (variations of 'John Smith')",
    "All created within 7 days",
    "Identical cash-out behavior"
  ]
}
```

---

### Pattern 2: Account Takeover (ATO)

**Description**: Fraudster gains access to legitimate user's account

**Graph Signature**:
```
Victim Account (normal history)
     |
     | [sudden change at timestamp T]
     |
     ├─── New Device (never seen before)
     ├─── New IP (different country)
     └─── New Transaction Pattern (large cash transfers)

Fraudster also controls other accounts:
Victim Account ----[new device]---- Fraud Account 1
                       |
                   [same IP]
                       |
                  Fraud Account 2
```

**Detection via ER**:
- Victim account should NOT be merged with fraud accounts (fraud contamination constraint)
- BUT we detect the linkage as a fraud signal
- Graph embeddings capture structural anomaly (victim account now connected to fraud cluster)

**Entity Resolution Output**:
```json
{
  "entity_id": "ATO_VICTIM_789",
  "primary_account": "victim_account_123",
  "alert_type": "account_takeover_suspected",
  "confidence": 0.88,
  "evidence": [
    "Impossible geolocation: US to Russia in 10 minutes",
    "New device first seen at takeover timestamp",
    "Weak graph connection to known fraud cluster",
    "Transaction pattern anomaly: $5000 transfer (avg is $50)"
  ],
  "action": "freeze_account_pending_verification"
}
```

---

### Pattern 3: Fraud Ring (Organized Network)

**Description**: Coordinated group running payment fraud operation

**Graph Signature**:
```
Coordinator
    |
    ├─── Mule 1 ----[receives]----> Victim 1
    |                                   |
    ├─── Mule 2 ----[receives]----> Victim 2
    |                                   |
    └─── Mule 3 ----[receives]----> Victim 3
           |
      [cashes out to crypto]

All mules share:
- Same IP range (VPN provider)
- Similar device fingerprints (emulators)
- Same registration timestamp window
```

**Detection via ER**:
- Entity resolution links Mule 1, 2, 3 as related (same operator)
- Graph embeddings capture circular transaction pattern
- Community detection identifies the fraud ring cluster

**Entity Resolution Output**:
```json
{
  "entity_id": "FRAUD_RING_456",
  "accounts": ["mule_1", "mule_2", "mule_3", "coordinator"],
  "confidence": 0.95,
  "fraud_pattern": "fraud_ring",
  "cluster_size": 4,
  "evidence": [
    "All accounts share IP subnet: 203.0.113.0/24",
    "Device fingerprints indicate Android emulators",
    "Circular transaction pattern detected",
    "All accounts created within 48 hours",
    "High graph embedding cohesion (0.91)"
  ],
  "victims": ["victim_1", "victim_2", "victim_3"],
  "total_fraud_amount": "$15,000",
  "action": "close_all_accounts_notify_law_enforcement"
}
```

---

## Key Features for P2P Payment Entity Resolution

### Behavioral Features (Critical for Fraud Detection)

#### Transaction Velocity
```python
velocity_24h = count(transactions in last 24 hours)
velocity_1h = count(transactions in last 1 hour)

if velocity_1h > 10:
    fraud_risk += "high_velocity_abuse"
```

#### Transaction Amount Distribution
```python
amounts = [t.amount for t in user.transactions]
avg_amount = mean(amounts)
std_amount = std(amounts)

# Fraudsters often use round amounts
if count(round_amounts) / total_transactions > 0.8:
    fraud_risk += "round_amount_pattern"
```

#### Recipient Diversity
```python
unique_recipients = len(set(t.receiver_id for t in user.transactions))
total_transactions = len(user.transactions)

diversity_ratio = unique_recipients / total_transactions

# Low diversity = potential money mule (always sends to same person)
if diversity_ratio < 0.1 and total_transactions > 20:
    fraud_risk += "low_recipient_diversity"
```

#### Login Pattern Anomalies
```python
login_hours = [t.hour for t in user.login_events]
typical_hours = mode(login_hours)  # e.g., 9am-5pm for normal user

# Sudden shift to 2am-4am logins = potential ATO
if recent_logins_outside_typical_hours > 0.8:
    fraud_risk += "login_pattern_anomaly"
```

---

### Device & Network Features

#### Device Fingerprint Consistency
```python
devices = user.devices_used
primary_device = most_common(devices)

device_consistency = count(primary_device) / total_sessions

# Fraudsters rotate devices frequently
if device_consistency < 0.3:
    fraud_risk += "device_hopping"
```

#### IP Geolocation Stability
```python
locations = [ip.geolocation for ip in user.ip_addresses]
unique_countries = len(set(loc.country for loc in locations))

# Legitimate users typically use 1-2 countries max
if unique_countries > 5:
    fraud_risk += "excessive_geo_diversity"
```

---

## Performance Considerations for P2P Payments

### Latency Requirements

| Operation | Max Latency | Rationale |
|-----------|-------------|-----------|
| **Real-time fraud check** | 200ms | Must not slow down payment flow |
| **Batch entity resolution** | 5s per 1000 records | Overnight batch processing |
| **Fraud ring detection** | 60s per block | Investigative use case |

### Scalability

**Expected Volume**: 1M+ users, 10M+ transactions/day

**Optimization Strategy**:
1. **Pre-blocking**: Use email domain, phone prefix, device fingerprint for blocking
2. **Incremental updates**: Only re-resolve entities when new data arrives
3. **Distributed processing**: Parallelize across blocks
4. **Caching**: Cache feature extraction and embeddings

---

## Compliance & Privacy

### Data Retention

- **PII**: Hash sensitive fields (email, phone, SSN) for linking, store separately
- **Transaction data**: Retain for 7 years (financial regulation)
- **Fraud investigations**: Preserve full graph for 5 years

### Privacy Considerations

- **GDPR right to be forgotten**: Support entity deletion and re-computation
- **PCI DSS**: Never store full credit card numbers in ER system
- **Explainability**: Always provide human-readable explanation for fraud decisions

---

## Monitoring & Alerting

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Precision** | >95% | <90% |
| **Recall** | >85% | <80% |
| **False Positive Rate** | <5% | >10% |
| **Processing Latency** | <5s | >10s |
| **Large Cluster Detection** | Flag >20 | Auto-alert >50 |
| **Constraint Violation Rate** | <2% | >5% |

### Fraud-Specific Alerts

1. **Large cluster detected** (potential fraud ring)
2. **High-confidence ATO** (immediate account freeze)
3. **Rapid cluster growth** (新emerging fraud pattern)
4. **Constraint violation spike** (data quality issue)

---

## Next Steps for Implementation

1. ✅ **Configuration defined** - `p2p_payment_resolution.yaml` created
2. **Implement constraint engine** with payment-specific logic
3. **Add behavioral feature extraction** (transaction velocity, patterns)
4. **Integrate fraud pattern detection** (circular transfers, fan-out)
5. **Build monitoring dashboard** with fraud-specific metrics
6. **Test on real payment data** with labeled fraud cases

---

This domain specification ensures the entity resolution system is optimized for P2P payment fraud detection while maintaining the core principles of correctness, explainability, and production safety.
