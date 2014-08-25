SemanticSky
===========



SemanticSky is a program which, given as input a set of documents, outputs a small multi-agent system where some built-in algorithmic agents try to infer similarity relations (currently, only content/topic similarity) between the input documents.

The main steps through which this is achieved follow:


. First, each document is transformed into a {\bf Cloud}: an object which theoretically should encapsulate all the information we can extract from the base document. Examples include: names of people mentioned in the document, names of places, statistically frequent word and frequently co-occurring (at a sentence level) pairs of words.
.  Secondly, these clouds are pairwise evaluated by a list of algorithms called {\bf Guardian Angels} which try to judge their similarity based on different and possibly complementary criteria.
. Finally, the evaluations of the Guardian Angels are merged into a single one, which represents the final state of the system, at this stage.

When the system is first initialized, or when a new document is added to the corpus, this is all there is to it.

But then, some more things will happen, as Agents (true people) evaluate by themselves the appropriateness of a link or the relevance of a tag or keyword to some page.

. The current state of the system is kept under watch on by a supervisor algorithm called  God, is judged either stable or unsettled. If some part of the network is unsettled, then God waits for more discussion to happen between agents and maybe even fuels it by suggesting relevant links to the parties involved or informing the parties of the presence of a third option, and so on...
. Once the system settles on some decision, such as the complete relatedness of two items, or maybe even the plain equivalence of two approaches that just happened to go under different names, then God gives feedback to all agents involved (human or algorithmic) regarding the accuracy of their guesses relative to the final state. This way, suggestion-givers who gave bad suggestions will be taken less into account in the future.


Crucially, the supervisor algorithm will need to 'suspend judgement' on user-backed agents while a discussion is still going on, so that plain democracy will decide on the final state of the system (the objective is to respect people's suggestions, not to distort them) without being influenced by the feedback they received. God is not a moderator: is a plain container and merger of opinions. He listens to the discussion and takes notes. On the other hand it's up to him to judge whether an algorithm is good or not.

Currently it's very easy to implement a new algorithm in the system,but not all algorithm are good, and most are good just on very specific subsets of the system. Suppose that we have an algorithm that just checks whether the authors of the document are the same person (and does that by regex matching some query). This algorithm will then return zero for all documents where an 'author' is not defined or the query doesn't match. God then will (try to) understand that the algorithm is useful in some subdomain, even though his average accuracy is very low.

The evaluations that a Guardian Angel performs differ from those of an human agent only in that they are produced automatically. Their route is in fact basically the same: they either get queued and later on processed by God, or (by default) they get immediately processed.

The `processing' implemented is currently quite naive. When an agent has a suspect strong x about the similarity of two documents y=sim(a,b), a ``Clue'' is spawned that conveys the information that the agent has an opinion x about the fact y.

Once the clue gets read by God, he will log it and then retrieve all logs about y; that is, all the information he has about y. Then, he will retrieve all the confidences of the clues (how strongly who produced them believed into them) and the weights (how well their authors usually do at guessing).

The weighted confidences are then averaged, and God's belief about x is updated to the thus obtained value.

Once the system reaches a stable situation about some fact y, the supervisor algorithm will hand out feedback to all the algorithms which had some suggestions about y or the discussion surrounding it. We can in fact imagine that, taken any pair of documents, there will be some arguments in favour and some against their similarity or relevance to one another. Not unlike what goes on behind a Wikipedia page (in the 'discussion' section), people will be allowed to debate about various issues, such as pertinence of tags, of links, and in general, let us say, the structure of the network. 
Once the discussion is over (this can be detected by, for example, a month of silence in the discussion page), the system will then adjust the weights of the Guardian Angels' future suggestions. For example, suppose that an algorithm gave particularly good suggestions in this situation (but not in many others); God will then try to guess what is that the algorithm (and maybe even the agent) is good and bad about, and adjust his weights selectively, not unlikely what goes on in the so-called Stacked Generalization models and Mixture of Experts models, which together with bayesian networks or neural networks are the (hem) nearest neighbours of SemanticSky.