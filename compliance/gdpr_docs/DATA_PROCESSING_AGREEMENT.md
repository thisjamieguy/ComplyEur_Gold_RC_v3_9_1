# Data Processing Agreement (DPA)
## ComplyEur - EU Trip Tracker

**Version:** 1.0  
**Date:** 2025-01-XX

---

## Parties

**Data Controller:** [Your Organization Name]  
**Address:** [Organization Address]  
**Contact:** [Contact Email]

**Data Processor:** [If applicable - third-party service provider]  
**Address:** [Processor Address]  
**Contact:** [Processor Contact]

---

## 1. Definitions

- **"GDPR"** means the General Data Protection Regulation (EU) 2016/679
- **"Personal Data"** means any information relating to an identified or identifiable natural person
- **"Data Subject"** means the individual whose personal data is processed
- **"Processing"** means any operation performed on personal data (collection, storage, use, etc.)

---

## 2. Subject Matter and Duration

### 2.1 Subject Matter
This DPA governs the processing of personal data by the Data Processor on behalf of the Data Controller for the purposes of:

- Employee travel tracking and compliance monitoring
- EU/Schengen 90/180-day rule compliance
- HR administrative functions

### 2.2 Duration
This agreement remains in effect for the duration of the service provision and until all personal data is returned or deleted as per Article 3.6.

---

## 3. Nature and Purpose of Processing

### 3.1 Personal Data Processed
- Employee names
- Travel records (countries, entry/exit dates)
- Trip purposes (optional)

### 3.2 Purpose of Processing
- Compliance with EU/Schengen travel regulations
- HR management and reporting
- Audit trail maintenance

### 3.3 Categories of Data Subjects
- Employees whose travel is being tracked
- Administrators with system access

---

## 4. Obligations of the Data Processor

### 4.1 Processing Instructions
The Processor shall:
- Process personal data only in accordance with documented instructions from the Controller
- Not process personal data for any purpose other than those specified in this DPA
- Immediately inform the Controller if instructions violate GDPR

### 4.2 Security Measures
The Processor shall implement appropriate technical and organizational measures:

- **Encryption:** AES-256-GCM encryption at rest
- **Access Control:** Role-based access control (RBAC)
- **Session Management:** Secure session cookies (HttpOnly, SameSite=Strict)
- **Audit Logging:** Immutable audit trail with integrity checking
- **Backup Security:** Encrypted backups with integrity verification
- **Network Security:** Firewall, WAF, TLS 1.3
- **Vulnerability Management:** Regular security scanning

### 4.3 Confidentiality
The Processor shall:
- Ensure persons authorized to process personal data are bound by confidentiality
- Not disclose personal data to third parties without Controller's consent
- Return or delete all personal data upon termination

### 4.4 Assistance to Controller
The Processor shall assist the Controller in:
- Responding to Data Subject Access Requests (DSARs)
- Ensuring compliance with GDPR Articles 32-36
- Providing necessary information for data protection impact assessments
- Notifying the Controller of personal data breaches without undue delay

### 4.5 Sub-processors
- The Processor may engage sub-processors only with Controller's prior written consent
- Sub-processors must be bound by the same data protection obligations
- The Processor remains fully liable for sub-processor compliance

### 4.6 Data Protection Impact Assessment
The Processor shall assist the Controller in carrying out data protection impact assessments when required under Article 35 GDPR.

---

## 5. Obligations of the Data Controller

### 5.1 Lawful Basis
The Controller warrants that:
- Processing has a lawful basis under Article 6 GDPR
- Processing complies with applicable data protection laws
- Data subjects have been informed of processing (Privacy Policy)

### 5.2 Instructions
The Controller shall:
- Provide clear, documented processing instructions
- Ensure instructions comply with GDPR
- Notify Processor of any changes to instructions

### 5.3 Data Subject Rights
The Controller is responsible for:
- Responding to data subject requests (access, rectification, erasure, etc.)
- Implementing data subject rights (Articles 15-22 GDPR)

---

## 6. Data Subject Rights

### 6.1 Assistance
The Processor shall assist the Controller in enabling data subjects to exercise their rights:

- **Right of Access (Article 15):** Provide data export functionality
- **Right to Rectification (Article 16):** Enable data correction
- **Right to Erasure (Article 17):** Enable data deletion
- **Right to Data Portability (Article 20):** Export in machine-readable format

### 6.2 Processor Obligations
The Processor shall:
- Notify Controller promptly of data subject requests
- Not respond directly to data subjects (unless authorized by Controller)
- Implement technical measures to support data subject rights

---

## 7. Data Breach Notification

### 7.1 Processor Obligations
The Processor shall:

1. **Immediate Notification:** Notify Controller without undue delay (within 24 hours) of any personal data breach
2. **Breach Details:** Provide:
   - Nature of breach
   - Categories and approximate number of data subjects affected
   - Categories and approximate number of records affected
   - Likely consequences
   - Measures taken or proposed to address the breach

### 7.2 Controller Obligations
The Controller is responsible for:
- Notifying supervisory authority within 72 hours (if required)
- Notifying affected data subjects (if high risk)

---

## 8. International Transfers

### 8.1 Transfers
- Personal data shall not be transferred outside the EEA without Controller's consent
- If transfers occur, Processor shall ensure adequate safeguards:
  - Standard Contractual Clauses (SCCs)
  - Adequacy decisions
  - Binding Corporate Rules (BCR)

### 8.2 Current Status
- **Storage Location:** EU-based server
- **No International Transfers:** Data remains within EEA

---

## 9. Data Retention and Deletion

### 9.1 Retention Period
- **Default:** 36 months after trip exit date
- **Configurable:** Retention period can be adjusted
- **Automatic Purge:** Data automatically deleted after retention period

### 9.2 Deletion Obligations
Upon termination of this DPA, the Processor shall:
- Return all personal data to Controller, or
- Delete all personal data (at Controller's choice)
- Provide certification of deletion
- Delete copies and backups (with secure overwrite)

---

## 10. Audit and Compliance

### 10.1 Audit Rights
The Controller has the right to:
- Audit Processor's compliance with this DPA
- Request documentation of security measures
- Request evidence of data protection compliance

### 10.2 Processor Obligations
The Processor shall:
- Maintain records of processing activities (Article 30 GDPR)
- Provide audit logs upon request
- Cooperate with supervisory authority inspections

### 10.3 Certifications
The Processor may demonstrate compliance through:
- ISO 27001 certification
- SOC 2 Type II reports
- Third-party security audits

---

## 11. Liability and Indemnification

### 11.1 Liability
Each party shall be liable for:
- Breaches of GDPR obligations
- Unauthorized processing
- Data breaches caused by their negligence

### 11.2 Indemnification
The Processor shall indemnify the Controller for:
- Costs arising from Processor's breach of this DPA
- Fines imposed by supervisory authorities due to Processor's breach

---

## 12. Termination

### 12.1 Termination
This DPA terminates when:
- The main service agreement terminates
- Either party gives 30 days' written notice
- Required by law or supervisory authority

### 12.2 Post-Termination
Upon termination, Processor shall:
- Cease all processing
- Return or delete all personal data
- Delete all copies and backups
- Provide certification of deletion

---

## 13. Governing Law

This DPA shall be governed by:
- **EU:** Law of [EU Member State]
- **UK:** Law of England and Wales

---

## 14. Signatures

**Data Controller:**

Name: _________________________  
Title: _________________________  
Signature: _________________________  
Date: _________________________

**Data Processor:**

Name: _________________________  
Title: _________________________  
Signature: _________________________  
Date: _________________________

---

**This Data Processing Agreement complies with Article 28 GDPR and ensures that personal data processing is carried out in accordance with applicable data protection laws.**

