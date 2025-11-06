1. **Data Minimization Principles**

We collect only the data essential for platform functionality: your username, password, and optionally your email for two-factor authentication. With JWT authentication with automatic token expiration, Argon2 password/PIN hashing, and complete absence of tracking cookies or analytics. We've deliberately chosen higher development complexity to achieve lower user privacy risk.

## **2\. Information We Collect**

### **2.1 Account Information**

* **Username:** Unique identifier chosen during registration, publicly visible in discussions  
* **Password:** Stored using Argon2 hashing algorithm, never stored in plain text   
* **Email Address:** Optional, collected only when you enable two-factor authentication   
* **Two-Factor Authentication Data:** Encrypted PIN codes and/or email verification tokens when enabled

### **2.2 Content and Activity Data**

* **Forum Contributions:** Posts, comments, replies, and edits you make in discussions   
* **Source Submissions:** Citations, metadata, excerpts, and descriptions you provide for sources **Ratings and Interactions:** Your ratings of sources, comments, and other user contributions   
* **Moderation Actions:** Reports you submit and moderation decisions if you have moderator privileges   
* **Article Access Records:** Specific discussions you've accessed through validated referrer links from publisher websites, including timestamp and source publication (retained to preserve your access privileges \- essential for contract performance \- never shared with publishers in identifiable form)

### **2.3 Access and Authentication Data**

* **Article Access Records:** Specific discussions you've accessed through validated referrer links from publisher websites, including timestamp and source publication **Authentication Tokens:** JWT access and refresh tokens for session management (automatically expire) **Session Data:** Login timestamps and authentication state for active sessions

### **2.4 Technical and Security Data**

* **Rate Limiting Information:** Temporary counters tracking your posting frequency and resource usage with the following limits to prevent abuse:   
  *  General platform actions: 1,000 requests per day   
  * User registration: 100 attempts per day   
  * Login attempts: 200 attempts per hour   
  * Source creation: 500 sources per day   
  * Comment posting: 2,000 comments per day   
  * Article creation: 200 articles per day   
  * Rate limiting data is automatically deleted after 1 day  
* **Error Logs:** Technical errors related to your account functionality (automatically anonymized) **Security Events:** Failed login attempts, password changes, and other account security activities **Rate Limiting Data:** Cryptographically hashed IP address identifiers stored for maximum 1 day to prevent abuse and enforce usage limits

### **2.5 Essential Cookies and Similar Technologies**

* **Authentication Cookies:** HttpOnly, secure cookies storing JWT tokens for session management **Security Cookies:** CSRF protection tokens and similar security mechanisms 

### **2.6 Data We Explicitly Do Not Collect**

* We do not collect, store, or process: IP addresses beyond temporary rate limiting (retained for maximum 1 day in hashed form), browsing behavior across other websites, location or geolocation information, device fingerprints or hardware identifiers, social media profile information, or third-party tracking data for advertising or behavioral profiling.  
* **Local Storage for Preferences**: User preferences are stored in user accounts for authenticated users only

## **3\. How We Use Your Information**

### **3.1 Platform Functionality**

**User Authentication:** Verifying your identity, managing login sessions, and maintaining account security **Access Control:** Validating your access to restricted discussions through publisher referrer verification **Content Management:** Displaying your contributions with proper attribution and enabling content editing **Community Features:** Facilitating discussions, source sharing, and user interactions within forums **View Count Generation:** Creating aggregate view counts for discussions and articles displayed to users (derived from access records, no additional personal data collected)

### **3.2 Communication and Notifications**

**Account Security:** Sending two-factor authentication codes and security alerts when enabled **System Communications:** Notifying you of policy changes, service updates, or account-related issues **Moderation Communications:** Informing you of content moderation decisions affecting your contributions

### **3.3 Security and Abuse Prevention**

**Rate Limiting:** Preventing spam, abuse, and automated attacks through temporary usage monitoring: Limits apply per user account (when authenticated) or per IP address (for anonymous users); Rate limits may be adjusted for operational needs without prior notice, with changes communicated through policy updates **Content Moderation:** Reviewing reported content and taking appropriate moderation actions **Account Protection:** Detecting unauthorized access attempts and suspicious account activity **Platform Integrity:** Maintaining discussion quality and preventing manipulation of source ratings

### **3.4 Service Improvement**

**Technical Maintenance:** Diagnosing and resolving technical issues affecting your account or content **Feature Development:** Understanding usage patterns to improve existing features (through anonymized data only) **Security Enhancement:** Identifying and addressing potential security vulnerabilities

### **3.5 Analytics**

Since we are a small experimental project, analytics will help tune the site to be more useful. These analytics will constitute **aggregate quantification** of site’s use, not tracking individual users. 

**Aggregate Usage Analytics**: We collect anonymized, aggregate data about site usage including page views, discussion participation rates, and feature usage patterns to improve platform functionality 

**View Count Generation**: Individual article view counts are generated from access records without storing additional personal data

**Technical Performance**: We monitor site performance, error rates, and technical issues through anonymized system metrics 

**No Individual Tracking**: All analytics are aggregated and anonymized—we do not create individual user profiles or track personal browsing behavior

## **4\. Information Sharing and Disclosure**

### **4.1 No Commercial Data Sharing**

**Absolute Prohibition:** We never sell, rent, lease, or otherwise commercially transfer your personal information **No Advertising Partners:** We do not share data with advertising networks, data brokers, or marketing companies **No Analytics Sharing:** We do not provide user data to third-party analytics or tracking services **Revenue Independence:** Our planned revenue model does not involve personal data monetization

### **4.2 Publisher Relationships**

**Referrer Validation Only:** We share only technical validation data with publishers to confirm legitimate access   
**Aggregated Analytics Only** Publishers may receive anonymized, aggregated metrics about discussion participation for their articles  
**No Personal Information:** Publishers never receive your username, email, or content contributions **Access Notification:** Publishers may receive aggregated, anonymized metrics about discussion participation **Partnership Changes:** publishers may request to change access of users with respect to moderation policy. 

### **4.3 Legal and Safety Disclosures**

**Legal Obligations:** We may disclose information when required by valid legal process (subpoenas, court orders, search warrants) **Emergency Situations:** We may disclose information to prevent imminent harm to persons or property **Law Enforcement:** We cooperate with law enforcement investigations involving genuine threats or illegal activity **Transparency Reporting:** We maintain records of legal requests and will publish transparency reports as legally permitted

### **4.4 Service Providers and Technical Disclosure**

**Infrastructure Partners:** Hosting providers and technical service providers access data only as necessary for service operation under strict confidentiality agreements **Security Consultants:** Security auditors and consultants may access data solely for security assessment purposes **Legal Advisors:** Attorneys and legal advisors may access data for legal compliance and dispute resolution

### **4.5 Business Transitions**

**Nonprofit Conversion:** During our planned transition to nonprofit status, user data protection remains unchanged **Asset Transfer:** In any business sale or transfer, user privacy commitments will be binding on successors **Service Discontinuation:** If we cease operations, we will provide advance notice and data export options before any data transfer

## **5\. Data Retention and Deletion**

### **5.1 Account Data**

**Personal Information Retention**

* Username, email address, and authentication credentials are retained only while your account remains active  
* Two-factor authentication data (PIN codes and email verification tokens) are retained only while 2FA is enabled  
* Account data is permanently deleted immediately upon account deletion

**User-Initiated Account Deletion**

* Account deletion is available through your account settings with a two-step confirmation process  
* You will be shown the impact of deletion on your contributions before final confirmation  
* Account deletion requires typing "DELETE\_MY\_ACCOUNT" as final confirmation  
* Once deleted, your account cannot be recovered

**Data Portability**

* You can view all personal data we store about you through your account settings  
* You can export your contributions and account data in a standard format before deletion  
* Export includes your forum posts, source submissions, connections, and ratings

### **5.2 Content Contributions**

**Discussion Preservation**

* Forum posts, comments, and replies remain visible indefinitely to preserve discussion integrity and context for other users  
* Source submissions and connection explanations remain available indefinitely to maintain research value  
* Upon account deletion, your username is replaced with "\[deleted\]" and content text is replaced with "\[deleted\]" placeholders

**Attribution Handling**

* Original authorship attribution is preserved in the form of "\[deleted\]" placeholders rather than complete removal  
* This approach maintains discussion threading, reply context, and citation integrity  
* Metadata such as post dates and discussion structure remain intact

**Content Modification Rights**

* User posts like sources and comments may or may not be deleted depending on moderation rules of a given thread, and UI implementation. 

### **5.3 Technical Data**

**Authentication and Session Data**

* Active JWT access tokens expire automatically after 30 minutes  
* Refresh tokens expire after 7 days and are automatically cleaned up  
* Blacklisted tokens (from logout) are cleaned up after their natural expiration period  
* Django session data is cleaned up daily for expired sessions  
* Django session data is cleaned up daily (1-day retention)  
* Anonymous session data expires after 24 hours

**Security and Monitoring Data**

* Rate limiting counters are automatically cleared after 1 day  
* Authentication logs and middleware functions are retained for 30 days for security monitoring  
* General application logs are retained for 90 days for technical maintenance  
* Error logs are retained for 180 days for debugging purposes and may contain request details  
* During early development phase, account deletion results in immediate removal from active database; users will be notified if/when backup retention policies become active

**Article Access Records**

* Records of which articles you've accessed through external url referrer validation are retained indefinitely: this preserves your access privileges to restricted discussions even after the original referrer session expires  
* Access records enable you to return to all discussions for articles you've legitimately accessed

**IP Address Processing for Rate Limiting**

* IP addresses are collected solely for rate limiting and abuse prevention   
* IP addresses are immediately combined with session identifiers and cryptographically hashed   
* Original IP addresses are never stored—only privacy-protecting hashes are retained   
* Hashed rate limiting data is automatically deleted after 1 day   
* Rate limiting periods vary by action type (hour/day) but all underlying data expires within 1 day maximum

### **5.4 Automated Data Cleanup**

**Regular Maintenance**

* Expired session data is automatically cleaned up daily  
* Old log files are automatically removed according to their respective retention periods  
* Rate limiting counters are automatically reset according to configured time windows  
* No user action is required for routine data cleanup

**Retention Period Changes**

* We may adjust technical data retention periods for operational needs without prior notice  
* Any changes to personal data retention periods will be communicated through policy updates  
* Account data and content retention policies require user notification for material changes

### **5.5 Data Deletion Limitations**

**Technical Constraints**

* Deleted content may persist in database backups for up to 90 days before backup rotation  
* Content cached by search engines or web archives is beyond our control  
* Discussion context preservation may prevent complete content removal in some cases

**Legal Obligations**

* Some data may be retained longer if required by legal process or ongoing investigations  
* We will notify affected users when legally permitted if extended retention is required  
* Data subject to legal holds will be clearly identified and segregated from routine processing

### **5.6 Account Deactivation vs. Deletion**

**Temporary Deactivation**

* Account deactivation is not currently supported \- contact us if you need temporary access suspension  
* Users requiring temporary breaks from the platform should consider not logging in rather than account deletion

**Permanent Deletion Effects**

* Account deletion is irreversible and immediate for personal data  
* Your access to restricted discussions will be permanently lost  
* Previously submitted sources and connections will remain but show as "\[deleted\]"

## **6\. Your Privacy Rights**

### **6.1 Account Control**

**Profile Management**

* **Username Modification**: You can change your username at any time through your account settings. Username changes do not affect the attribution of your existing content, as all contributions are internally linked to your unique user ID rather than your display name  
* **Email Address Management**: You can add, modify, or remove your email address through your account settings. Email addresses are only used for two-factor authentication when enabled  
* **Two-Factor Authentication Control**: You can enable, disable, or modify your 2FA settings at any time, including changing between PIN-based, email-based, or combined authentication methods  
* **Password Changes**: You can change your account password through your account settings using your current password for verification

**Account Deletion**

* **Two-Step Deletion Process**: Account deletion requires a two-step confirmation process to prevent accidental deletion  
* **Deletion Impact Review**: Before deletion, you will see exactly what content and access privileges will be affected  
* **Final Confirmation Requirement**: You must type "DELETE\_MY\_ACCOUNT" as final confirmation to complete the deletion process  
* **Immediate Personal Data Removal**: Upon deletion, your username, email, password, and all personal authentication data are immediately and permanently removed  
* **Content Preservation**: Your forum posts, source submissions, and connection explanations remain visible but are attributed to "\[deleted\]" to preserve discussion integrity and research value for the community

### **6.2 Data Access and Portability**

**Account Data Viewing**

* **Real-Time Access**: You can view all personal data we store about you through your account settings at any time  
* **Data Summary Display**: Your account page shows your profile information, content contribution counts, and active privacy policy consents  
* **Content History**: You can review all forum posts, source submissions, connections, and ratings you have created through the platform interface

**Data Export and Portability**

* **Data Export on Request**: Until automated export functionality is implemented on your account page, you can request a complete export of your personal data and contributions by contacting us. We will provide this data in a standard, machine-readable format within 30 days of your request  
* **Export Content Scope**: Data exports include your profile information, all forum posts and comments, source submissions with metadata, connection explanations, ratings given, and account activity timestamps  
* **Future Automated Export**: We are developing automated data export functionality that will be accessible directly through your account settings

**Data Correction Rights**

* **Content Editing**: You can edit your own forum posts, comments, and source submissions through the platform interface  
* **Profile Data Correction**: You can directly modify your username and email address through your account settings  
* **Content Moderation**: Platform moderators may edit content for policy compliance.   
* **Correction Requests**: For data accuracy issues you cannot resolve through normal editing functions, you can contact us with specific correction requests

### **6.3 Communication Preferences**

**Future Communication Scope**

* **Two-Factor Authentication**: When 2FA is enabled, you will receive PIN codes or email verification messages as needed for account security  
* **Account Security Alerts**: You may receive notifications about password changes, login from new locations, or other security-relevant account activity  
* **Policy Updates**: You will be notified of material changes to this privacy policy or terms of service  
* **Email Notification System**: We plan to implement optional email notifications for forum activity, source discussions, and platform updates  
* **Granular Preference Controls**: Future implementation will allow you to control specific types of notifications and their delivery methods  
* **Opt-Out Protections**: When expanded communication features are implemented, you will have granular control over notification types, with easy opt-out mechanisms for non-essential communications

**Communication Opt-Out**

* **Essential Communications**: Certain security-related communications cannot be disabled while your account remains active, including password reset confirmations and critical security alerts  
* **Optional Communications**: All non-essential communications (when implemented) will include clear unsubscribe mechanisms  
* **Account-Level Opt-Out**: Complete communication opt-out is available through account deletion

## **7\. Security Measures**

### **7.1 Technical Safeguards**

**Authentication Security**

* **Argon2 Password Hashing**: All passwords are hashed using the Argon2 algorithm, recognized as the current industry standard for secure password storage. Passwords are never stored in plain text  
* **Two-Factor Authentication Hashing**: User-chosen PIN codes are also hashed using Argon2 for additional security  
* **JWT Token Security**: Session management uses JSON Web Tokens with automatic expiration (30 minutes for access tokens, 7 days for refresh tokens) and token blacklisting upon logout  
* **Secure Session Management**: All authentication cookies are set with HttpOnly and Secure flags, preventing client-side access and ensuring transmission only over encrypted connections  
* **No Preference Cookies**: We do not use cookies or browser storage for interface preferences

**Communication Security**

* **HTTPS Encryption**: All data transmission between your browser and our servers is encrypted using HTTPS with modern TLS protocols  
* **HTTP Security Headers**: Our servers implement comprehensive security headers including Content Security Policy, X-XSS-Protection, X-Content-Type-Options, and HTTP Strict Transport Security  
* **CSRF Protection**: Cross-Site Request Forgery protection is implemented through secure tokens for all state-changing operations

**Infrastructure Security**

* **Rate Limiting**: Automated systems prevent abuse through intelligent rate limiting on posting, authentication attempts, and resource usage  
* **Secure Server Configuration**: Our servers are configured with security best practices, including regular security updates and monitoring  
* **Database Security**: All database operations use parameterized queries to prevent injection attacks, with access restricted to essential operations only

### **7.2 Data Protection**

**Data Access Controls**

* **Principle of Least Privilege**: All system components operate with minimal necessary permissions and access rights  
* **Administrative Access Logging**: All administrative access to user data is logged and monitored for security purposes  
* **Automated Security Monitoring**: Our systems continuously monitor for unusual access patterns, failed authentication attempts, and potential security threats

**Data Storage Security**

* **Temporary IP Processing**: IP addresses are collected only for rate limiting and abuse prevention, immediately hashed for privacy protection, and automatically deleted after 1 day  
* **No Permanent IP Logging**: IP addresses are not permanently stored and are only used temporarily for rate limiting and abuse prevention  
* **Anonymized Technical Logs**: Some system logs are automatically anonymized to remove personal identifiers while maintaining functionality for security monitoring and technical maintenance  
* **Secure Data Handling**: All personal data handling processes are designed to minimize exposure and follow secure coding practices

**Vulnerability Management**

* **Regular Security Updates**: All system dependencies and infrastructure components are regularly updated to address known security vulnerabilities  
* **Security Auditing**: We conduct regular security reviews of our codebase and infrastructure to identify and address potential vulnerabilities  
* **Incident Response**: We maintain procedures for rapid response to potential security incidents, which will include user notification protocols when legally permitted and appropriate

## **Section 8: International Compliance and Legal Framework**

### **8.1 Legal Basis for Processing**

**Primary Legal Bases**

We process your personal data under the following lawful bases as defined by applicable privacy laws:

* **Contract Performance**: Processing your username, password, authentication data, and forum contributions is necessary to provide our platform services as agreed in our Terms of Service  
* **Legitimate Interest**: We process technical data, security logs, and rate limiting information based on our legitimate interest in maintaining platform security, preventing abuse, and ensuring service stability. We have assessed that these interests do not override your privacy rights given our minimal data collection approach  
* **Consent**: When you enable two-factor authentication, we process your email address and PIN codes based on your explicit consent. You may withdraw this consent at any time through your account settings

**Article Access Records \- Indefinite Retention**

* **Legal Basis**: Contract Performance (GDPR Article 6(1)(b)) \- Indefinite retention of article access records is necessary to perform our service contract with users  
* **Purpose**: Enabling users to return to discussions for articles they've legitimately accessed without requiring repeated referrer validation  
* **User Benefit**: Once you've accessed an article discussion through legitimate publisher referrer, you retain permanent access to that discussion  
* **Legitimate Interest**: Platform maintains legitimate interest in preserving referrer validation system integrity and ensuring consistent user experience  
* **User Control**: Users can delete their account to remove access records, though this permanently removes access to all previously accessible discussions

**Special Category Data**

We do not intentionally collect special category personal data (sensitive personal data such as health, political opinions, or religious beliefs). If such information is inadvertently included in your forum contributions, you are responsible for its inclusion and can edit or delete such content.

### **8.2 International Data Transfers**

**Current Data Location**

* All user data is currently stored and processed within the United States on servers operated by our hosting provider  
* We do not currently transfer personal data outside the United States for processing purposes  
* Technical support and development activities are conducted within the United States

**Future International Operations**

* **Expansion Procedures**: If we expand operations internationally, we will implement appropriate safeguards including adequacy decisions, Standard Contractual Clauses, or other legally recognized transfer mechanisms  
* **User Notification**: We will update this privacy policy and notify users before implementing any international data transfers  
* **Data Localization**: We may offer data localization options for users in jurisdictions with specific requirements

**Cross-Border Access**

* Your forum contributions may be accessible globally through our public platform  
* We implement technical measures to prevent unauthorized international access to personal authentication data  
* Publishers validating access may be located internationally, but receive only technical validation data, not personal information

### **8.3 Regional Privacy Law Compliance**

**European Union (GDPR)**

* **Legal Representative**: Until we establish EU operations, users may contact us directly for GDPR-related requests  
* **Supervisory Authority**: EU users have the right to lodge complaints with their local data protection authority  
* **Data Protection Officer**: Given our minimal data processing scope, we do not currently require a Data Protection Officer but will appoint one if legal thresholds are met

**California (CCPA/CPRA)**

* **Consumer Rights**: California residents have rights to know, delete, correct, and opt-out of sale/sharing of personal information. We do not sell or share personal information for commercial purposes  
* **Non-Discrimination**: We do not discriminate against users exercising their privacy rights  
* **Third-Party Requests**: We do not honor third-party CCPA requests without proper verification of authority

**Other Jurisdictions**

* **Adaptive Compliance**: We monitor emerging privacy legislation and adapt our practices to maintain compliance  
* **Local Law Conflicts**: When local laws conflict with our privacy practices, we will either implement local accommodations or restrict service availability in that jurisdiction  
* **User Notification**: We will inform users of any jurisdiction-specific limitations or enhanced protections

  ### **8.4 Data Breach Notification and Contact Information**

**Breach Detection and Response**

* **Incident Monitoring**: We maintain automated systems to detect potential security incidents and unauthorized access to personal data  
* **Response Timeline**: Upon discovering a personal data breach, we assess the risk to users' rights and freedoms and take immediate containment measures  
* **Documentation**: All security incidents are documented with details of the breach, affected data, and remedial actions taken

**Supervisory Authority Notification**

* **Legal Compliance**: We notify the relevant data protection supervisory authority within 72 hours of becoming aware of a breach likely to result in risk to users' rights and freedoms, as required by GDPR Article 33  
* **Required Information**: Breach notifications include the nature of the breach, categories and approximate number of affected users, likely consequences, and measures taken or proposed to address the breach  
* **Follow-up Communications**: We provide additional information to supervisory authorities as our investigation progresses

**User Breach Notification**

* **High-Risk Threshold**: When a breach is likely to result in high risk to your rights and freedoms, we will notify you without undue delay as required by GDPR Article 34  
* **Notification Method**: User breach notifications are displayed through prominent site-wide banners that remain visible until acknowledged or for a minimum of 30 days  
* **Banner Characteristics**: Breach notification banners are non-dismissible, clearly marked as legal/compliance notices, and contain plain language descriptions of the incident  
* **Alternative Contact**: Given our minimal email collection, site banners serve as our primary notification method. Users without regular site access may contact us directly for breach information

**Notification Content Standards**

* **Plain Language Requirement**: All breach notifications use clear, non-technical language to describe the nature of the breach and its likely consequences  
* **Specific Information**: Notifications include the categories of personal data affected, measures taken to address the breach, and contact information for further inquiries  
* **Remedial Guidance**: When appropriate, breach notifications include specific steps users can take to protect themselves from potential consequences

**Privacy Contact Information**

* **Primary Contact**: \[Email placeholder \- to be filled before publication\]  
* **Response Time**: We respond to privacy-related inquiries within 30 days, or sooner as required by applicable law  
* **Breach Inquiries**: Users affected by security incidents may contact us directly for specific information about their personal data involvement  
* **Verification**: Privacy requests may require identity verification to protect against unauthorized access

**Complaint Procedures**

* **Internal Process**: Users may first contact us directly to resolve privacy concerns, including breach-related complaints  
* **Supervisory Authorities**: Users in applicable jurisdictions have the right to lodge complaints with their local data protection authority without prejudice to other legal remedies  
* **Escalation**: Unresolved complaints may be escalated to appropriate dispute resolution mechanisms as outlined in our Terms of Service

### **8.5 Cross-Border Law Enforcement**

**Legal Process Requirements**

* **Valid Legal Process**: We require proper legal process (subpoenas, court orders, search warrants) before disclosing user information to law enforcement  
* **Jurisdictional Review**: We review foreign legal requests for compliance with applicable treaty obligations and local law  
* **User Notification**: We notify affected users of legal requests when legally permitted and practically feasible

**Emergency Situations**

* **Imminent Harm**: We may disclose information without legal process when necessary to prevent immediate physical harm  
* **Documentation**: All emergency disclosures are documented and reviewed for legal compliance  
* **Transparency Reporting**: We maintain records of law enforcement requests for inclusion in future transparency reports

### **8.6 Compliance Monitoring and Updates**

**Regular Review Process**

* **Legal Updates**: We monitor changes in international privacy legislation and update our practices accordingly  
* **Compliance Audits**: We conduct regular internal reviews of our privacy practices against applicable legal requirements  
* **External Assessment**: We may engage third-party privacy professionals for compliance verification as our operations scale

**Policy Update Procedures**

* **Material Changes**: Significant privacy policy changes will be communicated to users with appropriate notice periods as required by applicable law  
* **Version Control**: We maintain version history of our privacy policy with effective dates clearly marked  
* **Grandfathering**: Existing users' rights will be preserved during policy transitions unless enhanced by new protections

**International Expansion Safeguards**

* **Privacy Impact Assessments**: We will conduct privacy impact assessments before expanding to new jurisdictions with complex privacy requirements  
* **Legal Compliance**: International expansion will include local legal review to ensure full compliance with applicable privacy laws  
* **User Choice**: Users will be informed of any changes to data handling resulting from international expansion

## **9\. Business Model Evolution**

### **9.1 Nonprofit Commitment**

**Fundamental Not-for-Profit Mission**

PublicSphere operates as a public benefit platform dedicated to improving democratic discourse through evidence-based discussion. Regardless of our legal organizational structure at any given time, our mission and operations will always prioritize public benefit over profit maximization. We are committed to operating as a not-for-profit entity in practice, even during periods when our legal status may be sole proprietorship or other transitional structures.

**Organizational Transition Timeline**

We plan to transition to formal nonprofit legal status as our platform scales and resources permit. This transition timeline is flexible and will be determined by operational needs, funding requirements, and community growth. During any transitional period, our privacy protections, data handling practices, and user rights will remain unchanged or be enhanced.

### **9.2 Service Evolution**

### **Service Pricing Change Procedures**

Currently, PublicSphere operates as a free platform. If we introduce any paid features or services in the future to users: **Free Service Preservation**: Core discussion and source-sharing functionality will remain freely available regardless of any premium feature additions. 

**Feature Modification Rights During Business Transitions**

* **Core Functionality Protection**: Essential platform features including article discussions, source submissions, and forum participation will be preserved during any business model changes  
* **Enhancement Focus**: Business model evolution will prioritize feature enhancement rather than feature restriction  
* **User Notification**: Material changes to existing features will be communicated with appropriate notice periods and user input opportunities

### **9.3 Data Handling During Organizational Changes**

**Privacy Protection Continuity**

* **Data Handling Consistency**: Our minimal data collection approach and privacy protections will be maintained or enhanced during any organizational transitions  
* **User Rights Preservation**: All user privacy rights, data access capabilities, and account control features will be preserved during business model changes  
* **Policy Binding**: Any successor organization or legal structure will be bound by existing privacy commitments to users

**Nonprofit Transition Procedures**

* **Asset Transfer Protections**: During nonprofit incorporation, user data and privacy commitments will be transferred with full protection integrity  
* **Board Governance**: Upon formal nonprofit status, user privacy protection will be incorporated into organizational governance documents  
* **Transparency Commitment**: The nonprofit transition process will be documented and communicated transparently to users

## **10\. Contact and Enforcement**

### **10.1 Privacy Questions and Requests**

**Primary Contact Information**

* **Privacy Inquiries**: publicspherestaff@gmail.com  
* **General Support**: publicspherestaff@gmail.com  
* **Data Requests**: publicspherestaff@gmail.com  
* **Security Issues**: publicspherestaff@gmail.com

**Response Time Commitments**

* **Standard Inquiries**: We respond to privacy-related inquiries within 30 days of receipt  
* **Data Access Requests**: Personal data access requests are fulfilled within 30 days  
* **Account Deletion Requests**: Account deletion requests are processed immediately upon verification  
* **Security Incidents**: Security-related inquiries receive priority handling within 144 hours

**Request Verification Procedures**

* **Identity Verification**: Privacy requests may require verification of account ownership to protect against unauthorized access  
* **Account-Based Verification**: Verification typically involves demonstrating access to the account in question  
* **Documentation Requirements**: Complex requests may require additional documentation for proper processing

### **10.2 Policy Updates and Changes**

**Notification Methods for Policy Changes**

* **Site-Wide Banners**: Material privacy policy changes are announced through prominent, non-dismissible site banners  
* **Email Notification**: Users who have provided email addresses may receive direct notification of policy changes  
* **Banner Duration**: Policy change notifications remain visible for a minimum of 10 days  
* **Archive Access**: Previous policy versions are maintained for user reference

**Effective Date Procedures**

* **Notice Period**: Material changes to privacy practices require a 10-day notice period before implementation  
* **Immediate Changes**: Changes that enhance user privacy protections may be implemented immediately with notification  
* **User Consent for Reductions**: Policy changes that would reduce existing privacy protections require explicit user consent

**Granular Change Communication**

* **Specific Impact Description**: Policy update notifications clearly describe what changes and how it affects users  
* **Plain Language Requirement**: All policy change communications use clear, non-technical language  
* **Contact Availability**: Users can contact us during policy change periods for clarification

### **10.3 Complaint Procedures and Dispute Resolution**

**Internal Complaint Process**

* **Direct Resolution**: Users may contact us directly to resolve privacy concerns and complaints  
* **Response Timeline**: We acknowledge privacy complaints within 48 hours and provide resolution status within 7 days  
* **Escalation Options**: Unresolved complaints can be escalated through multiple contact attempts and detailed documentation

**External Complaint Options**

* **Supervisory Authorities**: Users in applicable jurisdictions have the right to lodge complaints with their local data protection authority  
* **Consumer Protection**: Users may also contact relevant consumer protection agencies regarding privacy practices  
* **Legal Remedies**: Complaint procedures do not limit users' legal remedies under applicable privacy laws

**Documentation and Follow-up**

* **Complaint Records**: We maintain records of privacy complaints and resolutions for transparency and improvement purposes  
* **Resolution Communication**: Complaint resolutions are communicated clearly with specific actions taken or explanations provided  
* **Prevention Measures**: Systemic issues identified through complaints are addressed through policy or technical improvements

## **11\. Technical Implementation Details**

### **11.1 Cookie Policy and Essential Technologies**

**Essential Analytics and Measurement**

PublicSphere implements privacy-preserving analytics to improve platform functionality:

* **View Count Analytics**: Aggregate view counts for articles and discussions (no individual user tracking)  
* **Site Traffic Measurement**: Anonymized traffic patterns and usage statistics for platform optimization  
* **Performance Monitoring**: Technical performance metrics and error tracking for service improvement  
* **No Third-Party Tracking**: We do not use third-party tracking cookies, advertising cookies, or behavioral profiling technologies  
* **No Cross-Site Tracking**: We do not participate in cross-site tracking networks or data sharing for advertising purposes

**Essential Cookies and Similar Technologies**

PublicSphere uses only essential cookies required for platform functionality. These cookies cannot be disabled while using the site, as they are necessary for core operations:

* **Authentication Cookies**: HttpOnly, secure cookies storing JWT access and refresh tokens for user session management. Access tokens expire after 30 minutes, refresh tokens expire after 7 days  
* **Security Cookies**: CSRF protection tokens and security mechanisms to prevent cross-site request forgery attacks

**Cookie Security Characteristics**

* **HttpOnly Flag**: Authentication cookies are set with HttpOnly flags, preventing client-side JavaScript access for enhanced security  
* **Secure Flag**: All cookies are transmitted only over encrypted HTTPS connections  
* **SameSite Protection**: Cookies include SameSite attributes to prevent cross-site request forgery attacks  
* **Automatic Expiration**: Session cookies are automatically cleaned up upon expiration

**No Tracking or Analytics Cookies**

* **No Third-Party Tracking**: We do not use any third-party tracking cookies, analytics cookies, or advertising cookies  
* **No Behavioral Profiling**: We do not implement any technologies for behavioral tracking or user profiling  
* **No Cross-Site Tracking**: We do not participate in cross-site tracking networks or data sharing for tracking purposes

### **11.2 Server Logs and Technical Data**

**Anonymized Technical Logs**

* **Application Logs**: General application logs are retained for 90 days for technical maintenance and debugging purposes  
* **Error Logs**: Error logs are retained for 180 days for technical issue resolution and may contain request details  
* **Security Logs**: Authentication and security-related logs are retained for 30 days for security monitoring  
* **Automatic Anonymization**: System logs are automatically configured to exclude or anonymize personal identifiers where possible

**Rate Limiting Privacy Protections**

* **Privacy-Protective IP Processing:** Rate limiting systems immediately hash IP addresses combined with session identifiers using cryptographic hashing (MD5). Original IP addresses are never stored. Hashed identifiers are automatically deleted after 1 day regardless of rate limiting period (hour/day/week).  
* **Temporary Storage**: Rate limiting counters are automatically cleared on a short-term basis and are not permanently stored  
* **No Permanent IP Logging**: IP addresses are not permanently stored beyond temporary rate limiting requirements

**Log Data Cleanup Procedures**

* **Automated Cleanup**: Expired log files are automatically removed according to defined retention periods without requiring manual intervention  
* **Retention Period Adherence**: Log cleanup processes strictly adhere to the retention periods specified in our data retention policies  
* **Secure Deletion**: Log file deletion processes ensure data cannot be recovered after the retention period expires

### **11.3 Database and Session Management**

**Session Data Handling**

* **Django Session Management**: User sessions are managed through Django's built-in session framework with automatic cleanup of expired sessions  
* **Daily Cleanup**: Expired session data is automatically cleaned up daily through automated maintenance processes  
* **JWT Token Blacklisting**: Logout actions result in JWT token blacklisting, with blacklisted tokens cleaned up after their natural expiration period

**Database Security Measures**

* **Parameterized Queries**: All database operations use parameterized queries to prevent SQL injection attacks  
* **Access Controls**: Database access is restricted to essential operations only, following the principle of least privilege  
* **Backup Security**: Database backups are encrypted both in transit and at rest, with deleted user data potentially persisting in backups for up to 90 days before rotation

**Technical Data Retention Automation**

* **Automated Maintenance**: All technical data cleanup processes are automated and require no user action  
* **Operational Adjustments**: Technical data retention periods may be adjusted for operational needs without prior notice  
* **User Notification**: Material changes to personal data retention policies will be communicated through policy updates

## **12\. Children's Privacy and Age Requirements**

### **12.1 Age Verification and Eligibility**

**Minimum Age Requirement**

PublicSphere requires all users to be at least 16 years of age. During account registration, users must confirm they meet this age requirement by checking a verification box confirming they are 16 years of age or older. This age requirement is set to provide enhanced privacy protections for younger users while enabling meaningful participation in evidence-based discussions.

**Account Creation Safeguards**

* **Age Confirmation Required**: Account registration cannot be completed without explicit confirmation of meeting the minimum age requirement  
* **Terms Agreement**: Users aged 16 to 17 but over 16 must independently agree to our Privacy Policy and Terms of Service  
* **Enhanced Protection**: Users aged 16 to 17 receive the same privacy protections as all users, with additional safeguards applied to account management

### **12.2 Enhanced Protections for Minors**

**Data Collection Limitations for Minors**

* **Minimal Data Collection**: Our standard minimal data collection approach provides additional protection for users aged 16 to 17   
* **No Profiling**: We do not create behavioral profiles or detailed user analytics for any users, providing particular protection for younger users  
* **Communication Restrictions**: Optional email collection for users aged 16 to 17  is limited to essential account security functions only

**Parental Rights and Notification**

* **Account Independence**: Users aged 16-17 may create and manage accounts independently without parental consent under our terms  
* **Privacy Requests**: Privacy-related requests for users aged 16 to 17 may be submitted by the user directly through our standard contact procedures  
* **Account Deletion**: Users aged 16 to 17  may independently request account deletion through our standard account deletion procedures

### **12.3 Content and Interaction Safeguards**

**Educational Context Protections**

* **Source-Based Discussions**: The platform's emphasis on source materials and evidence-based discussion provides a structured, educational environment  
* **Transparent Attribution**: All user contributions are attributed, promoting accountability and responsible participation  
* **Academic Integrity**: The platform's focus on source verification and citation promotes academic integrity and responsible information sharing  
* **Community Standards**: Community guidelines emphasize respectful, evidence-based discussion suitable for educational environments

**Safety and Reporting Mechanisms**

* **User Reporting**: All users, including those aged 16 to 17, have access to reporting mechanisms for inappropriate content or behavior

