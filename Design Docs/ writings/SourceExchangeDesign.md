PublicSphere: SourceExchange forums

Explainer Text for Clients

The high-level design:   
	PublicSphere hosts specialized discussions that are a natural extension of sources, footnotes, and an author’s deliberately designed discussions connected to an article. In addition to “regular” forum structure, Publicsphere allows readers to add their own sources as part of the discussion, structured to be commented on and referenced in their own right. 

Function:   
Articles often have footnotes and sources. With news distrust statistically very high, well-researched sources of information are an important way for readers to ensure that an article is grounded in fact. PublicSphere deepens this interaction, hosting specialized forums and reader discussions around the author’s sources, giving readers the tools to do their own thinking. What’s more, it can give skeptical readers the tools to change their minds. In including reader forums to these sources, these diverse readers can educate each other, disagree, and provide new sources and evidence that can heighten their understanding, and potentially find a more nuanced conclusion together. As the author of an article using PublicSphere, in your writing or footnotes, you can ask for reader opinions, personal testimony, or research, dictating the structure of the discussion you would like, and PublicSphere will host it. At your request, we can add moderation abilities to your account for discussions hosted for your writing. These discussion forums are user-first tools for communication and exploration, and will be expanded as the site grows.   
Text for the Website  
Part 1:   
“Digital journalism isn't just about writing anymore—it's about creating spaces for meaningful conversation. In today's complex information landscape, traditional reporting struggles to keep pace with rapidly evolving events. PublicSphere's SourceExchange bridges this gap by empowering authors to create structured, evidence-based discussions that extend naturally from their written work.

SourceExchange grounds journalism in verifiable truth by connecting readers directly to sources and fostering transparent dialogue. Authors who embrace this platform understand that openness to scrutiny and willingness to revise incorrect assertions aren't just noble ideals—they're essential practices of responsible journalism in the digital age."

Part 2:   
“SourceExchange transforms the traditional relationship between authors and readers by creating dedicated spaces for evidence-based discussion. At its core, SourceExchange extends the concept of footnotes and citations into interactive forums where readers can engage directly with sources, contribute their own evidence, and participate in structured dialogue.

Authors can design specialized discussions connected to their articles, giving readers tools to explore, verify, and expand upon the original reporting. These customizable forums allow for various types of engagement \- from source verification and additional evidence submission to personal testimonies and expert commentary. The flexible tab system accommodates different discussion needs and levels of moderation, with options including Sources, General Discussion, Reader Topics, Author Questions, and Reader Experiences.

The platform's architecture ensures that discussions remain connected to their parent articles while maintaining accessibility. Readers gain access through direct links from the original article, and for subscribers of publications with paywalls, this creates a secure and seamless transition from reading to participation without compromising publisher boundaries.

Layout: 

The author must include links to the PublicSphere site to direct readers, or can collaborate with Publicsphere to create a button or visual tag for their website that will take users to the discussion page. 

**Header:** Has coloration menu (for darkmode and cream-color-mode). 

	SourceExchangePage:  
**Sub-Header:** Each article has its own subheading with the article Title, and below that tabs.   
Tabs: 

1. Sources  
2. General  
3. Reader’s topics  
4. Author Asks  
5. Give your Experience  
6. More  
   These tabs can be added or removed depending on author’s specifications, and if they only use PublicSphere for sources, the tabs disappear.   
   Below The tabs, is the tab’s contents, including the source discussion, i.e. a list of Notebook 12-like components. 

**Site Structure and Access System**  
By default, a user has access to only the default forums and readable pages that PublicSphere offers, as well as the pages for articles that are not restricted access, which and gains access to restricted articles’s forums by using the link within the article itself. PublicSphere will have a page with the links to all hosted articles. They can also access forums via the correct URL if that forum does not have restricted access. If there is restricted access to an article, i.e. a paywall:   
When a reader clicks a link to PublicSphere forums from an article, our system verifies they came directly from the authorized publisher's website by checking the HTTP referrer header. Once verified, access to that specific forum is automatically granted and stored—both in the browser session for visitors and permanently in the user's account data for registered members. This ensures readers can always return to discussions for articles they've legitimately accessed, while maintaining publisher content boundaries.

**An author can create a discussion structure with a footnote.**  

1. They can start a comments section under a question.   
2. They can ask for sources.   
3. They can ask for personal testimony. The latter lends itself to local issues. 

**Discussion Specification options for authors (require additional resources):** 

1. Allowing certain file types (not in initial release)  
2. Allowing Argument Maps  (not in initial release)  
3. Moderation level

### **Moderation System**

We’ll have a post-publication moderation framework focused on community-driven reporting and administrator intervention. Similar to Reddit's approach, content is published immediately and can be removed by moderators based on user reports or direct moderation. The system supports temporary or permanent user bans, comment removal, and comprehensive moderation logs to track all actions taken.

### **Moderator Security**

Moderator privileges are protected by a strict security model where the MODERATOR server database can only be modified by administrators through secure, authenticated channels. The system employs multiple authentication factors for administrative access, with encrypted user data, audit logging of all privilege changes, and automated security checks to detect and prevent unauthorized moderator assignments. This ensures that moderation capabilities remain strictly controlled by the site administrator.

## **Source Duplication Prevention System**

The system implements a multi-step verification process when users create source areas. First, it checks for exact matches using URL normalization and DOI comparison. If no exact match exists, it performs fuzzy matching on title and author fields using trigram similarity. Before final creation, users see a confirmation screen with potential matches, showing similarity scores and highlighting matched fields. Users can either select an existing source or confirm their submission is unique, with an option to explain why despite similarities.

## **OpenGraph Metadata Parser for Citation Generation**

The metadata parser extracts bibliographic information from web pages using a priority-based approach. It first attempts to extract structured data via OpenGraph, Twitter Cards, and Schema.org JSON-LD. For academic sources, it queries CrossRef or DataCite APIs using detected DOIs. The system maps extracted fields to source area database columns, automatically populating title, author, publication date, and publisher. For incomplete metadata, the interface highlights missing fields for manual completion while saving extracted data, with confidence indicators for each auto-filled field.

Additional Design choices:   
\- **Django’s JWT authentification**, shorter access tokens with loinger refresh tokens, blacklist after rotation, http only cookies, custom permission and tokens for moderators

**URL Perspective Design**  
PublicSphere has a homepage (PublicSphere)  
A homepage for the SourceExchange functionality (PublicSphere/sourcexchange)  
Article’s homepage (publicsphere/sourcexchange/\[articlename\])  
Specific source: ([https://publicsphere.fyi/sourcexchange/article-name\#tab=sources\&source=12](https://publicsphere.fyi/sourcexchange/article-name#tab=sources&source=12))  
Development Workflow: 

1. **Start with core backend development** \- Begin with your data models and API endpoints  
2. **Set up a basic Docker configuration**   
3. **Develop frontend components** \- Once your core API is functioning  
4. **Implement continuous integration early** \- Test deployments frequently  
5. **Refine and expand features** iteratively  
- Tailwind  
- Django packages like `drf-spectacular` or `drf-yasg` that can auto-generate OpenAPI specs from your Django REST Framework views.  
- For error handling, **Use Django's Logging System**: Leverage Django's built-in logging framework  
- Manual deployment strategy  
- **Database Migration Strategy:**   
  - **Schema as Code**: Define all database changes as code files (migrations) rather than manual SQL commands.  
  - **Sequential Versioning**: Number migrations sequentially so they're applied in the correct order.  
- Multi-tiered approach to rate limiting per user with respect to data types.  
- Unit testing for backend with django testing, API endpoint test, manual frontend testing. 

Frontend ToDo  
We’ll need to be sure that everything works well with mobile as well.   
React framework, tailwind when necessary

1. User registration (See Notes on Security below)  
   Registration requires:   
   	Username

		Password  
		Privacy Policy Accept toggle (to be filled out later)  
		OPTIONAL 2FA using  
			1\. PIN  
2\. Email option to be added later  
		

2. Create the Article Page functionality  
   1. Article text tied to source(s) with optional quote  
   2. Comments  
   3. Connection menu with comments and rating.   
3. Create a demo article that’s hosted on the site directly to test the Article Page functionality  
4. Create the other tabs.   
5. Get the user database running on some public server  
6. Host discussion for a professional article.   
7. Consider aesthetic and accessibility of design. Keyboard navigation, et.c

**\[**  
**Notes on Security:**  
\- Use secure password hashing algorithms   
\- Generate all security tokens and keys using cryptographically secure random generation

DATA MINIMIZATION:  
\- Collect only essential user data (username and password only)  
\- Do not log or store IP addresses permanently  
\- Configure server logs to exclude or anonymize personal identifiers  
\- Implement automatic deletion policies for any temporary data  
\- Do not use tracking cookies, analytics, or third-party tracking scripts

SECURE CODING PRACTICES:  
\- Validate and sanitize all user inputs to prevent injection attacks  
\- Use parameterized queries for all database operations  
\- Implement proper error handling that doesn't expose sensitive information  
\- Apply the principle of least privilege to all database operations  
\- Keep all dependencies updated and regularly scan for vulnerabilities

COMMUNICATION SECURITY:  
\- Enforce HTTPS across the entire site with proper certificate validation  
\- Implement HTTP security headers (Content-Security-Policy, X-XSS-Protection, etc.)  
\- Configure proper CORS settings to prevent unauthorized cross-origin requests  
\- Set secure and HttpOnly flags on cookies containing sensitive information  
\- Implement SameSite cookie attributes to prevent CSRF attacks

USER PRIVACY:  
\- Make privacy policy accessible, clear, and honest about minimal data collection  
\- Provide users with options to delete their accounts and associated data (comments  and posts will not be deleted)  
\- Do not share any user data with third parties  
\- Implement data backups with encryption  
\- Create a transparent process for handling any potential data breaches

The system must prioritize user privacy while maintaining necessary security to protect the integrity of discussions. All security measures should be implemented following current best practices without compromising the user experience.  
Questions: Why keep dependencies updated? What are session management tokens, and why must they be encrypted? )\]

Business strategy:   
1\. Begin by starting the website as “PublicSphere forums”, and creating article expansions for authors by:   
	a. Reaching out  
	b. General word-of-mouth  
Concurrently, develop PublicSphere article hosting, argument map hosting, improved UI, better and deeper participation, and more in a fluid roadmap. The priority is always to create a medium with ever-improving democratic, transparent, empirical and effective discourse.   
2\. For preliminary gov.t money paperwork, begin as a sole proprietor or independent contractor.   
3\. Transition to charging for services by those who approach, simply by covering the server costs, then as businesses and publications get involved, transition to getting volunteers onboard and file as a non-profit. 