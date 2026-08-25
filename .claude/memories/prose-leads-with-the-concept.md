# Prose leads with the concept

## Table of Contents

- [Who the reader is](#who-the-reader-is)
- [Lead with the point](#lead-with-the-point)
- [Concepts rather than identifiers](#concepts-rather-than-identifiers)
- [Use the exact term](#use-the-exact-term)
- [Name the subject exactly](#name-the-subject-exactly)
- [The reader's questions are the test](#the-readers-questions-are-the-test)
- [Vagueness is not knowing, dressed up](#vagueness-is-not-knowing-dressed-up)
- [One idea to a sentence](#one-idea-to-a-sentence)
- [Cut what changes nothing](#cut-what-changes-nothing)
- [Tables and bullets](#tables-and-bullets)
- [Showing a change](#showing-a-change)
- [Related notes](#related-notes)

## Who the reader is

Everything written here is read by somebody who was not in the conversation that produced it and does not have the files open. That covers an issue, a commit message, a comment on an issue and a reply in the session. Write for that reader.

There is a test for whether you did, and it is the one worth running before anything is filed. Read the whole thing back as though seeing it for the first time, and stop at every "the", every "its", and every verb with nobody doing it. The first two claim the reader already has the thing they point at. The third hides whoever acts: "one function inside that file is named as the entry point" says neither who names it nor how, where the answer was that a line in the deployment settings gives a file name and a function name, and Amazon reads it. Where they do not, the sentence is broken however ordinary its words are: "a Lambda function that creates its client" invites the reader to work out which client is the function's own, "the shared Python library" names a thing introduced nowhere, and a package whose name appears before anything has said what it is arrives as noise.

Run that pass over the whole thing after every edit, not over the sentence just changed. An edit breaks references in the paragraphs around it: "`aws_clients` is a place to keep them" read correctly in the draft where it was written, and lost what "them" pointed at when the paragraph above it was rewritten two edits later. A sentence that was right when written does not stay right.

Run the pass yourself rather than letting the reader run it. Nine separate sentences in one issue were caught this way by the person it was written for, one at a time, over nine turns, and every one would have failed the same read at the writer's desk.

## Lead with the point

Lead with the point. A paragraph opens on the thing it is there to say, and where that thing is a defect the first sentence says what is wrong, naming the subject as it says it.

This is a rule about order rather than a licence to explain. Background is whatever the reader needs in order to judge the claim, it goes under the claim rather than in front of it, and it is cut to the part the claim turns on. A definition of something the reader already knows is not background at all. An issue about pytest fixtures opened with a hundred words defining a fixture and describing how a test asks for one, and reached the defect in its second paragraph, where every reader who could act on that issue had known the first paragraph for years.

The rule this replaced asked a paragraph to say what the thing is and what it does before naming any file, function or line, which is two rules wearing one coat. Say what a defect costs near the top rather than in the seventh paragraph, and give the reader a subject before pointing at its parts. Neither of those asks for a paragraph of exposition ahead of the point, and read as a single rule that is what it produced.

## Concepts rather than identifiers

Write in concepts, not identifiers. Say what the code does and what goes wrong directly, without hedging. An argument about behaviour that only holds while the reader is looking at the file is one the reader cannot check. Identifiers belong where the reader has stopped reading and started working: the change being proposed, the file to edit, the function to delete.

Naming a place is not the same as naming a supporting cast, and a paraphrase of a location is usually vaguer than the location. "A package in the shared Python library" sent a reader looking for a library that has no name here, where `lib/python/` would have told them where to stand. Name a directory once, where the reader needs somewhere to picture, and then use it.

Writing in concepts is not writing in abstractions, and this is the way it goes wrong. Swapping a name for a compound noun makes a sentence vaguer, not clearer, because a name at least points at something: "a cached-client package sits in the shared Python library" says less than the package's own name would have. The thing a piece of writing is about may be named, once, so the reader knows what is under discussion. What is barred is the supporting cast — the other files, the functions, the line numbers — and the way out of a sentence full of them is to explain the idea, not to replace each name with a category.

## Use the exact term

A term from computer science is the name of a real thing, and naming the thing is the job. Module, handler, importer, exception, HTTP status code, Lambda function: each of these is written here, by name, wherever it is what the sentence is about, and said in passing the first time it appears. The test a word has to pass is whether it names what the sentence is about, not whether it belongs to this trade.

This section used to ask the opposite, and the writing got worse for it. It said that a term with a simpler-sounding equivalent was shorthand and lost to that equivalent, so "handler" became "the part of a file that runs when a request arrives", which is four times the length and leaves the reader nothing to search for. The substitute is usually not the same thing either: "the number" for an HTTP status code, "an error" for an exception and "an endpoint" for the Lambda function serving a route each say less than the term, and each sends the reader looking for something the writer did not mean. A sentence that reads as though the writer were avoiding the vocabulary of the subject is obscure, not accessible.

What is still barred is a word that promises a mechanism the reader will look for and not find, which is a question of what is true rather than of vocabulary. Python is interpreted and nothing is built, so a client that was "built" invites a search for a build step that does not exist; a line of code ran and returned a new client, and "created" says that. "Spun up", "compiled" and "wired" go the same way. The verb to use is the one that survives somebody asking what it means literally.

## Name the subject exactly

The rule against identifiers bars the supporting cast and never the subject. The thing a piece of writing is about is named, by its real name, in the first sentence that needs it.

Both rules were read together on 2026-08-23 and produced an issue about a Python exception that named neither the exception, nor the library that raises it, nor the code it carries. The route became "an endpoint here", which asked GitHub to cancel a workflow run, though a route asks for nothing and the function serving it does. Its three functions became "three of its functions", which a route does not have. The HTTP status code became "the number", and a status code in the 200s became "one number that means GitHub agreed". Three `if` bodies that no input can execute became "those checks were unreachable", with neither word explained. Six terms removed, six questions back from the reader, and every answer was a term the writer knew and had already read in the source.

## The reader's questions are the test

There is a second pass, and it catches what the cold read above does not. Take each noun phrase in turn and ask what it refers to, answering only from the sentence it sits in. "An endpoint" — the route, or the code serving it? "The number" — which number? "Those checks" — which checks, and unreachable in what sense? A phrase the sentence cannot answer is a term that was removed and has to go back.

Run it as well as the cold read rather than instead of it, because the two fail on different things. The cold read stops at every "the", every "its" and every verb with nobody doing it, and a vague noun goes through it untouched: "the number" carries a definite article, points at something introduced two sentences earlier, and is unreadable all the same.

The same defect over a whole document is a term used repeatedly and defined nowhere. One issue said "the rule" four times and never said what the rule was, then rested a sentence on the omission — what is left is the rule — which cannot be true of something that was never there. Both were found by the reader asking the question this pass asks: what rule?

## Vagueness is not knowing, dressed up

Every vague sentence written here has had one cause. The writer described a mechanism they had not checked, in words shaped like an explanation. Three came out of a single issue in a single session: a client became "a small helper object", the cost of creating one became "asking for one is not free", and the reason it costs anything became a library that "works out which credentials apply", which was invented. A euphemism, an empty pronoun and a fabricated mechanism are the same failure wearing three coats.

Write what can be stated concretely. Where it cannot be, find out; where it cannot be found out — the dependency is not on this machine and installing it is barred, see [verification-in-ci-only](verification-in-ci-only.md) — leave the detail out and say only what the repository itself makes true. A sentence about an outside library's internals is almost never load-bearing, and the version that survives the cut is usually the one the reader needed: creating a client takes time, and this package exists so the time is spent once.

The cure is not a longer list of banned words. Each of the three was caught and written down as its own rule, and each time the next sentence failed the same way in a new disguise, because the rules named symptoms and the cause was elsewhere. Ask what is actually known before reaching for a word that sounds like it explains.

Repeat the noun rather than reaching back for it with a pronoun. A reader who has to search backwards to find what "it" or "one" stands for is doing the work the writer skipped, and the search gets harder with every clause in between. The word "one" is the worst of them, because it is a counter as well as a stand-in.

## One idea to a sentence

One idea to a sentence. Do not chain subordinate clauses to fit a second idea in. This replaced an older rule that asked for simple, ordinary English, which turned out to constrain vocabulary and say nothing at all about length. It was satisfied for a long time by long clause-chained sentences built out of short words. A rule about the shape of a sentence is refusable in a way an adjective is not.

The shape that breaks it most often qualifies its subject twice before reaching a verb. "Sixty-four fixtures in the files pytest loads on its own, before running any test beneath them, are filed under one name and defined under another for a reason that does not hold in their file" opens an issue with five things at once: how many there are, where they live, when those files are read, what is written on them, and why it is wrong. The reader waits until halfway for a verb and gets a weak one. Each of the five is a sentence, and the first sentence only owed the reader one of them.

## Cut what changes nothing

A detail that changes nothing the reader would do is cut, table or not. A word budget was tried and dropped, because length was never the defect and density is. A cap punishes writing that genuinely needs the words and invites padding what does not.

## Tables and bullets

Tables are allowed where a table genuinely reads better than a paragraph: a name-to-name rename mapping, or two measured columns being compared. Bullets are allowed only when enumerating a list of things. Do not use bullets to break up an argument — an argument is prose.

## Showing a change

A change is shown to the reader rather than described to them. What a command printed does not reach them: the output of a tool call goes to the session and not into the conversation, so a diff read out of a tool result is a diff nobody has seen. Put it in the reply itself, inside a fenced `diff` block, which the terminal colours red and green the way git does.

Quoting the old and new text as block quotes instead was tried three times in one session and failed three times. It loses the colouring, loses the alignment that puts a changed line against the line it replaced, and takes more room to say less. Where a hunk carries long unchanged lines, cut them and say what the marker stands for, so the elision is not read as a deletion.

## Related notes

Nothing here is hard-wrapped — see [markdown-is-not-hard-wrapped](markdown-is-not-hard-wrapped.md). How these rules land on the seven sections of an issue, and which section carries the identifiers, is in [how-issues-are-written](how-issues-are-written.md).
