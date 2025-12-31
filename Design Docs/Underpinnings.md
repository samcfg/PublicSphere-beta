This is a tool for non-formal, pragmatic logic. While formal logic is deductive, relying on symbolic logic-crunching to generate valid argumentation, PublicSphere's syntax is simple, immediately readable, and tries to generate sound logic, sacrificing strict symbolic validity for inductive, *defeasible* (falsifiable) argumentation. In large argument maps, there may be sections of purely deductive reasoning, but for the sake of a unified design, formal logic is not used there, and it is up to users to describe their arguments clearly in connection notes and claim content. 
As far as ratings, I have had the idea that claims should not be manually rated, rather their ratings are generated as a compounding of source and connection ratings (perhaps with some algorithm that weights more heavily on sources, since there may be more or less of them, or weights sources and the overall chain of connections between the source and the claim in some ratio)? That design is subject to more thought. 
As far as circular reasoning, I think the creation of a circular connection should be banned. It is logically incongruous, and it short-circuits the calculation of claim ratings. 
Sources make the most sense as leaf nodes

  H2: "All arguments can be approximately represented in this schema if we
  accept:
  1. Loss of modal distinctions (necessity/contingency)
  2. Loss of probabilistic precision (unless Bayesian extensions are added)
  3. Implicit warrants must be made explicit in connections
  4. Rebuttals/defeaters are modeled as counter-claims rather than
  defeat-relations"

  H3: "The schema's philosophical foundation lies in:
  - Informal logic (Toulmin, Walton, Govier): argument as dialogical
  justification
  - Epistemological foundationalism: sources ground claims (but note: your
  graph structure also supports coherentism if circular justification is
  allowed)
  - Pragma-dialectics (van Eemeren & Grootendorst): argumentation as
  resolution of difference of opinion"

Interesting, I think that the community assessment is an imprecise measure of warrant. The counter argument 
is that it is too much of a social processess to arive at the rating, but since claims are a combination of 
their contributing connection and source ratings, a believer-on-faith of a claim would need to individually 
rate connections and sources to skew the rating, which is ultimately more unnatural than simply making up 
their mind. Thoughts on defining the rating as metric of collectively concieved warrant, aka justification for
 belief? 

I'd also like to introduce an inevitable problem: how to draw out the full argument into its elementary parts 
from one which is put into the schema improperly.
 I'll give the example of someone who says that (Source: john was divorced yesterday)-(connection: he got 
divorced yesterday, and since single people are bachelors, john is a bachelor)-> (claim: John is a bachelor) .
 In this example, if someone wanted to attack the argument on the basis that some single people might not be 
bachelorsf (eg. what if John is a woman?), the structure of the argument map would require the user to 
down-rate the connection, but that would be conflated with the other implicit argument that because john was 
divorced, they are now not married (not true of all cultures). We need some way to suggest edits which split 
poorly written connections into their component parts, if the situation warrants it. 
And also, there is the problem that any user can create a connection between nodes that should have several 
nodes between them, or perhaps they do but the fully laid-out argument can be circumvented by a poorly written
 one. But I suppose this is better supported by the normal rating system, by which people can downvote these 
poorly written connections in favor of ones that connect all the dots, which have more explanitory value.  
 
Finally, I'd like there to be a way to eventualy vet a logical necessity in the site, rendering a connection 
100% certain, like all bachelors are not married. Of course, given the site's pragmatic framing, a statement 
like that, merely a matter of definitions, is not so important to represent. so perhaps because tautologies 
are not of importance here, this logical necessity hardening is less important. 

Start with a response to the first concern, that of rating approximating warrant 

## Splitting/elaborating connections into component arguments
  Mechanism:
  1. User selects connection as "contains multiple inference steps"
  2. Proposes split: Source → [New Intermediate Claim] → Original Claim
     1. Views all paths from one claim to another to see current alternatives, reduce redundancy. Selects that for replacement, else: 
  3. Creates intermediate node (e.g., "John is now single")
  4. Community votes on whether split improves clarity
  5. If approved, replaces conflated connection with elaborated chain

  This is argument refactoring - restructuring for clarity without changing substance. Similar to your
  fork/modification system (12.12_Plan.md).

---

## Philosophical Frameworks in Conversation with PublicSphere

**1. Inferentialism (Robert Brandom)**
- Meaning constituted by inferential role: what follows from a claim, what it follows from, what's incompatible
- PublicSphere literally implements this: claims get meaning from graph position
- "Making It Explicit": Connection notes force articulation of implicit reasoning
- "Game of Giving and Asking for Reasons": The entire system formalizes this social practice
- Deontic scorekeeping: Tracking commitments/entitlements (though less applicable to defeasible empirical reasoning)

**2. Hermeneutics (Gadamer, Ricoeur)**
- Truth disclosed through interpretation and articulation, not just discovered
- Multiple valid articulations of same reality (different conceptual frameworks)
- "Fusion of horizons": Different perspectives encounter each other, understanding emerges through dialogue
- PublicSphere: Elaborated arguments make understanding explicit; diverse articulations represent different interpretive frameworks

**3. Epistemic Justice (Miranda Fricker)**
- Testimonial justice: All voices deserve epistemic credibility
- Hermeneutical justice: All communities need conceptual resources to articulate experiences
- PublicSphere: Valuing diverse articulations prevents hermeneutical injustice—marginalized groups can express arguments in their own terms

**4. Pragma-Dialectics (van Eemeren & Grootendorst)**
- Argumentation as resolution of difference of opinion through critical discussion
- Goal: Test claims against strongest objections, not "win" debates
- Truth emerges from dialectical process
- PublicSphere: Arguments refined through splitting, elaboration, counterarguments, community evaluation

**5. Informal Logic (Toulmin, Walton, Govier)**
- Real-world argumentation differs from formal deduction
- Toulmin's model: Claim, Data, Warrant, Backing, Qualifier, Rebuttal
- PublicSphere: Claim-Source-Connection is simplified syntax; warrants in connection notes; qualifiers/rebuttals emergent from graph structure

**6. Deliberative Epistemology (Habermas)**
- Public reason: Legitimate beliefs emerge from inclusive deliberation
- Discourse ethics: Truth claims must survive critical scrutiny from all perspectives
- Ideal speech situation: All participants can contribute, challenge, question
- PublicSphere: Collectively conceived warrant through community evaluation

### Supporting Frameworks

**7. Pragmatism (Dewey, Peirce)**
- Truth is what survives inquiry and testing (Peirce's "convergence of inquiry")
- Knowledge emerges from collaborative inquiry, not individual reflection (Dewey)
- PublicSphere: Ratings as formalized inquiry results; elaboration as iterative refinement

**8. Social Epistemology (Goldman, Longino)**
- Knowledge production is fundamentally social
- Justification emerges from community practices, not individual cognition
- Distributed cognitive labor: Different people evaluate different evidence
- PublicSphere: "Collectively conceived warrant" = social constitution of normativity

**9. Perspectivalism (Distinct from Relativism)**
- All knowledge is perspectival—shaped by standpoint, background, conceptual framework
- BUT: Perspectives can be evaluated for coherence, evidential support, explanatory power
- Truth requires integrating multiple perspectives, not selecting one
- PublicSphere: Multiple high-rated argument paths can coexist; diversity valued but evaluated

**10. Coherentism**
- Justification as mutual support within belief network, not foundational bedrock
- Truth is about systemic coherence, not correspondence to atomic facts
- PublicSphere: Graph structure supports coherentist reading (though empiricist grounding leans foundationalist)
- Tension: Sources as foundations vs. circular justification prevention

**11. Distributed Cognition**
- Cognitive processes distributed across individuals, tools, environments
- No single person has complete picture; understanding emerges from collective system
- PublicSphere: Argument graph is distributed cognitive artifact; ratings aggregate collective judgment

**12. Bayesian Epistemology**
- Degrees of belief (credences) updated via Bayes' Theorem: P(H|E) = P(E|H)×P(H)/P(E)
- Evidence provides warrant proportional to likelihood ratio
- PublicSphere: Ratings approximate credences but aren't formally Bayesian (future extension possibility)

**13. Epistemic Modal Logic**
- Formal treatment of knowledge (K), belief (B), justification (J)
- Epistemic necessity (□ₖP: must be true given knowledge) vs. possibility (◇ₖP: might be true)
- PublicSphere loses modal distinctions: Can't represent necessity vs. contingency, actual vs. possible

**14. Defeasible Reasoning**
- Conclusions can be retracted given new evidence (non-monotonic logic)
- Default rules with exceptions (birds fly, but penguins don't)
- PublicSphere: Contradictory connections model defeaters; ratings change as evidence evolves

### Contrasts (What PublicSphere Explicitly Rejects or Differs From)

**15. Logical Positivism**
- Truth = empirical verification via sense data
- Meaning = verification conditions
- PublicSphere: More social/hermeneutic; verification is collective, not individual sensory

**16. Naive Realism**
- Truth is directly accessible, transparently discovered
- No role for interpretation or articulation
- PublicSphere: Realist about facts, but hermeneutic about access—truth requires interpretive work

**17. Strong Relativism**
- All perspectives equally valid; no objective evaluation
- Truth relative to framework with no cross-framework standards
- PublicSphere: Evaluative non-relativism—ratings distinguish better from worse arguments

**18. Classical Deductive Logic as Universal**
- All reasoning reducible to formal deduction (premises → conclusion necessarily)
- PublicSphere: Focuses on inductive, abductive, defeasible reasoning; soundness over validity

---

## Conversation Context (December 2024)

### Topic
Philosophical and epistemological underpinnings of PublicSphere's claim-source-connection schema. Examining whether the schema captures the essence of rigorous argumentation and exploring its theoretical foundations.

### Key Discussions

**1. Schema vs. Classical Logic**
- PublicSphere is non-formal, pragmatic logic prioritizing soundness (true premises + good inference) over validity (correct form)
- Designed for defeasible empirical reasoning, not deductive certainty
- Claim-source-connection maps onto Toulmin's informal logic but simplifies syntax for usability

**2. Ratings as Collectively Conceived Warrant**
- Claim ratings computed from source + connection ratings (not directly user-rated)
- Forces engagement with argument structure (can't vote for conclusions without rating evidential components)
- Represents community's collective assessment of epistemic warrant/justification
- Socially constituted but structurally enforced (resistant to casual bias)

**3. Modal Distinctions Lost**
- Cannot represent necessity vs. contingency ("All bachelors are unmarried" vs. "Biden won 2020")
- Cannot represent actual vs. possible/counterfactual
- Ratings approximate epistemic probability but aren't formal Bayesian credences
- Acceptable trade-off for empirical factual domain ("Did X happen?")

**4. Connection Splitting/Elaboration**
- Problem: Conflated inference steps in single connection (divorced → single AND single → bachelor)
- Solution: Users suggest splitting connections into elementary steps with intermediate claims
- Path discovery interface shows existing elaborated alternatives to prevent duplication
- Better articulation favored by rating system (transparency > brevity)

**5. Graph Quality Control ("Chemical Kinetics")**
- Slow creation rate: Similarity checking, reputation gates, connection requirements, deposit/stake systems
- Speed removal rate: Auto-decay for low-rated/orphaned claims, redundancy detection, merge suggestions
- Goal: Equilibrium where high-quality claims persist, spam decays naturally
- Structural solutions preferred over moderation

**6. Brandom's Deontic Scorekeeping**
- Strict commitment tracking (you accept A→B and A, you MUST accept B) doesn't fit defeasible reasoning
- Users weigh competing evidence, have defeaters, hold probabilistic beliefs
- Adapted version: Soft coherence checking (inconsistency alerts), hypothetical exploration, recommendations
- Advisory, not mandatory—respects epistemic autonomy

**7. Dual Goals: Truth + Articulation**
- Epistemic: Seeking what's actually true (evidence-grounded)
- Hermeneutic: Representing diverse ways of understanding/articulating truth
- Better articulation isn't just instrumental—it's constitutive of understanding
- "Dialectical Hermeneutic Empiricism" or "Deliberative Epistemic Realism"

---

## Brief Summary for Future Context

PublicSphere is a collaborative argument mapping platform with claim-source-connection schema designed for empirical reasoning.

Ratings represent "collectively conceived warrant" (community assessment of evidential support), computed from source/connection ratings to force engagement with argument structure. The system values both truth-seeking (epistemic goal) and diverse articulation (hermeneutic/pluralistic goal).

Design prioritizes soundness over validity, defeasible reasoning over deduction, and material inference over formal logic. 