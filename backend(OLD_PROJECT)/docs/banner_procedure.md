Admin Breach Notification Procedure
Emergency Data Breach Response Protocol
Time-Critical Requirements: GDPR requires supervisory authority notification within 72 hours and user notification "without undue delay" when high risk exists.
Step 1: Initial Assessment (Within 1 Hour)

Document the incident: Record time of discovery, nature of breach, estimated number of affected users
Assess risk level: Determine if breach poses "high risk" to user rights and freedoms
Determine notification requirements:

Low risk: Supervisory authority only
High risk: Supervisory authority + user notification required



Step 2: Supervisory Authority Notification (Within 72 Hours)

Prepare required information per GDPR Article 33
Submit notification to relevant data protection authority
Document submission time and confirmation

Step 3: User Notification via Site Banner (If High Risk)
Login Process:

Navigate to https://[yourdomain]/admin/
Enter admin credentials
Navigate to Core > Site banners (/admin/core/sitebanner/)
Click Add Site Banner

Banner Configuration:

Title: "Data Security Incident Notification"

Message: "We experienced a data security incident on [DATE]. [BRIEF DESCRIPTION OF WHAT HAPPENED]. [WHAT DATA WAS INVOLVED]. We have taken immediate steps to secure our systems and are working with cybersecurity experts. No passwords or financial information were compromised due to our minimal data collection practices. You may contact us at [EMAIL] with questions. This notice will remain posted for 30 days as required by data protection regulations."

Severity: Legal/Compliance
Is active: ✓ (checked)
Is dismissible: ✗ (unchecked)
Expires at: [30 days from incident date]

Click Save
Verify banner appears immediately on main site