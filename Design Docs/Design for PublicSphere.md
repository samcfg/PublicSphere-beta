**Design for PublicSphere**

Overall Goals

- Be a useful tool for online social platform for responsible democratic deliberation, to fill the need for a reasonable way to understand both sides of a political argument. Instead of relying on the media’s take to decide that, we can all voice our opinions collectively. To do that you’ll need to limit the topic to demonstrable facts that can change a person’s epistemological view. That’s a big step from assuming anything can be misinformation, if you have reliable commentary from anyone all the time.   
- A forum which allows users to collaborate and share knowledge.  
- Instead of a structure to maximize time spent on the website, PublicSphere will incentivize truth.  
- Users will be able to submit a claim, and evidence to support it. This claim will then be tested by other users, and if it cannot be disproven, it might be true.  
- Logical structures of connected claims and evidence can get big, containing multiple sources and claims, potentially creating a cohesive argument. This argument can be criticized by readers by rating either the sources, claims or the connections.   
- These logical structures can be accompanied by a textual document written by the creator(s) of the structure.   
- The "claim", "evidence" system must be structured to optimize for rationality, empiricism, clarity and accessibility.  
- Factual and logical data will be assessed by AI assisted admins to ensure rigor.   
- The UI design should be minimalist, and exude an ethos of academia and creativity. 

Structure of PublicSphere

First of all, there are specific structures necessary for the website to function: 

1. Areas: a card-like shape containing text boxes and sometimes other files. Can be one of two types of area:   
   1. Source Areas: The top-right of the area displays the \*type of evidence\* (paper, article, first-hand, etc.). The evidence types have designated colors, where the “area” card has the color of the evidence type. The textboxes of the evidence area change with the type of evidence selected, but can include: title, followed by a written description, followed by author, author-given title, institution, issue and page number, year, and URL. There is also an option to submit a file.   
   2. Claims Areas: This is an area with only two textboxes: the title and the ‘falsifiable claim’  
2. Connections: Joins two or more \*areas\*. Once created, connections are displayed as a line with a "+" in the middle of the line. Users can add a propositional logic symbol to the line in place of the "+" to show how the text boxes logically connect. For example, a user could indicate that if both pieces of evidence that they submit are true, then the claim must be true. optionally with a symbol of propositional logic. When the logic symbol is directional (e.g. if area1 implies area2, the reverse is not true), this information is stored.   
3. User files: A storage system comprising files, areas, and pages.  
4. Pages: Users can create pages in their files, and title them. They can import areas onto the pages. The areas on the page can be moved around, and connections can be created between these areas. Areas from other user’s spaces or posts can be dragged and dropped into a user’s space, and a user can choose to make their space public.  The pages can be submitted as a post to the website’s forum. In pages, areas are displayed as cards, and the connections appear on the left margin of the screen. A user can create a document that goes with a page, where they explain in an article format their argument, and provide more nuance. 

Things you can do: 

- **Create source area:** A user can create and submit an “evidence area”.   The formatted source option is not mandatory for “first-hand” type evidence, otherwise all  textboxes are mandatory, at which point the “publish” button becomes active below the box. At the bottom of the box, there is an option to add a file. Once submitted, the evidence area becomes part of a user’s \*files\* within the website. A source area can be submitted as a post, and requested for verification.   
- Highlight source area: a quote can be highlighted from the original textual source, and displayed as a header at the top of a source card. This quote can be paraphrased by the user in this header as well.   
- Submit claim: A user can create a claim area by entering text. Under the prompt to create the claim text, there is a prompt to “add source” where the user can make a source area that connects to their claim on the same page. Once submitted, the claim area becomes part of a user’s \*files\* within the website.   
- Create a cross-referenced source area: A user can combine two highlighted source areas where the quotes are stating the same fact. The fact is then displayed at the top of an area, and the two source areas are shown at the bottom of this area as sub-areas.   
- Users can create as many pages as they want. From each page, a user can create areas, which are by default stored on the page which they are created. The areas on the page can be moved around, and connections can be created between these areas. Areas from other user’s spaces or posts can be dragged and dropped into a user’s space, and a user can choose to make their space public.   
- Request verification: for posted pages and posted evidence areas, a user can request verification, where an admin checks that the sources are plausible, the connections are logically sound, the claim(s) is/are falsifiable and supported, and that the format is properly done, and that the document is well-written and logically sound. The areas that are verified have a “verified” symbol, as do “review-in-progress” areas.   
- Interactable Post: Once a page has been posted, other users can interact with it. Users can submit rating numbers (0%-100%) for areas. These ratings are displayed on the bottom of each claim and evidence text box respectively, and beside each logical connection symbol. When clicked, the user can choose to rate or view the rating distribution graph, showing all user ratings, and the original poster’s rating the highest. There is a "comments" dropdown menu button on the bottom of each area, and the comments section is structured like that of reddit, with an upvotes system. That other user can interact with another's post in the following ways:  
1. A button saying "rate" is on the bottom of each claim and evidence text box respectively, and beside each logical connection symbol. They can rank their confidence in either the claim, evidence or logical connection. This confidence is submitted as a 0%-100% value on a sliding bar.  
2. In the "comments" dropdown menus, a user can participate in this forum.  
3. Below the last piece of evidence of the post, there is a button saying "suggest new evidence". If clicked, the user can submit an evidence area just like that of the poster. They must submit a logical connection with their suggested evidence. They can create their own area, or import if from their own files or from another user’s. The suggested evidence text boxes are displayed at the bottom of this webpage, with their logical connection lines extending to the original post. The suggested evidence can also be rated and commented on. If that evidence is popular enough, it goes to the admin for verification. If it is verified, it moves up the page to be directly below the original post, with a narrow line separating it from the original post.    
4. A collapsible forum titled "discussion" is below the post and above the suggested evidence that has not been verified. This operates the same as the other "comments", but serves as a general place for people to give impressions.  
5. A button to the right margin of the post's claim area says "submit counterclaim". The user can submit a new claim area, and indicate whether it is the logical negative of the original claim, an alternative, or simply adds nuance to the original. These can also be voted on with confidence indicators.

- Original Poster Modification: After verification, the original poster of a given post can request to change the post by the admin. These changes are recorded transparently to all users.

- LOGIN: Users can enter a username or password in order to submit claims and criticism.

- HOMEPAGE:  will display all posted pages. This has a search/filter functionality for claims and evidence. There are topic categories/tags for better organization. 

- Posted Evidence areas: these will have their own tab on the website. 

I’d also like to implement a way to facilitate bayesian analysis, where related claims are assigned probabilities, and evidence modifies the claims’ probabilities in a specific way.   
