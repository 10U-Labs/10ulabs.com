# Prose leads with the concept

## Table of Contents

- [Who the reader is](#who-the-reader-is)
- [Lead with what the thing is for](#lead-with-what-the-thing-is-for)
- [Concepts rather than identifiers](#concepts-rather-than-identifiers)
- [No jargon where a plain word will do](#no-jargon-where-a-plain-word-will-do)
- [Vagueness is not knowing, dressed up](#vagueness-is-not-knowing-dressed-up)
- [One idea to a sentence](#one-idea-to-a-sentence)
- [Cut what changes nothing](#cut-what-changes-nothing)
- [Tables and bullets](#tables-and-bullets)
- [Showing a change](#showing-a-change)
- [Related notes](#related-notes)

## Who the reader is

Everything written here is read by somebody who was not in the conversation that produced it and does not have the files open. That covers an issue, a commit message, a comment on an issue and a reply in the session. Write for that reader.

There is a test for whether you did, and it is the one worth running before anything is filed. Read the whole thing back as though seeing it for the first time, and stop at every "the" and every "its". Each one claims the reader already has the thing it points at. Where they do not, the sentence is broken however plain its words are: "a Lambda function that creates its client" invites the reader to work out which client is the function's own, "the shared Python library" names a thing introduced nowhere, and a package whose name appears before anything has said what it is arrives as noise.

Run that pass yourself rather than letting the reader run it. Five separate sentences in one issue were caught this way by the person it was written for, one at a time, and every one of them would have failed the same read at the writer's desk.

## Lead with what the thing is for

Lead with what the thing is for. A paragraph opens by saying what the thing is and what it does, before any file, function or line is named. Say what a defect costs in ordinary words near the top rather than in the seventh paragraph. Opening with the concept is not a licence to re-establish context the reader already has; leading and restating are different things.

## Concepts rather than identifiers

Write in concepts, not identifiers. Say what the code does and what goes wrong in plain words, without hedging. An argument about behaviour that only holds while the reader is looking at the file is one the reader cannot check. Identifiers belong where the reader has stopped reading and started working: the change being proposed, the file to edit, the function to delete.

Naming a place is not the same as naming a supporting cast, and a paraphrase of a location is usually vaguer than the location. "A package in the shared Python library" sent a reader looking for a library that has no name here, where `lib/python/` would have told them where to stand. Name a directory once, where the reader needs somewhere to picture, and then use it.

Writing in concepts is not writing in abstractions, and this is the way it goes wrong. Swapping a name for a compound noun makes a sentence vaguer rather than plainer, because a name at least points at something: "a cached-client package sits in the shared Python library" says less than the package's own name would have. The thing a piece of writing is about may be named, once, so the reader knows what is under discussion. What is barred is the supporting cast — the other files, the functions, the line numbers — and the way out of a sentence full of them is to explain the idea in ordinary words, not to replace each name with a category.

## No jargon where a plain word will do

Use a plain word wherever one exists. Jargon from computer science is not made acceptable by being accurate, and a reader who has to decode the first sentence has been handed the writer's job. Where a term genuinely has no plain equivalent, say what it means in passing the first time it appears.

Jargon is hard to see from the inside, because a word used every day stops feeling like a word that needs explaining. The test is to ask of each noun whether it names something outside this trade, and to treat every no as a word to replace or to explain where it first appears. "Module" is a file. "Handler" is the part of a file that runs when a request arrives. "Importer" is whatever uses the thing. Each of those was written here as though it were ordinary English, in a paragraph whose whole purpose was to be plain.

## Vagueness is not knowing, dressed up

Every vague sentence written here has had one cause. The writer described a mechanism they had not checked, in words shaped like an explanation. Three came out of a single issue in a single session: a client became "a small helper object", the cost of creating one became "asking for one is not free", and the reason it costs anything became a library that "works out which credentials apply", which was invented. A euphemism, an empty pronoun and a fabricated mechanism are the same failure wearing three coats.

Write what can be stated concretely. Where it cannot be, find out; where it cannot be found out — the dependency is not on this machine and installing it is barred, see [verification-in-ci-only](verification-in-ci-only.md) — leave the detail out and say only what the repository itself makes true. A sentence about an outside library's internals is almost never load-bearing, and the version that survives the cut is usually the one the reader needed: creating a client takes time, and this package exists so the time is spent once.

The cure is not a longer list of banned words. Each of the three was caught and written down as its own rule, and each time the next sentence failed the same way in a new disguise, because the rules named symptoms and the cause was elsewhere. Ask what is actually known before reaching for a word that sounds like it explains.

Repeat the noun rather than reaching back for it with a pronoun. A reader who has to search backwards to find what "it" or "one" stands for is doing the work the writer skipped, and the search gets harder with every clause in between. The word "one" is the worst of them, because it is a counter as well as a stand-in.

## One idea to a sentence

One idea to a sentence. Do not chain subordinate clauses to fit a second idea in. This replaced an older rule that asked for simple, plain, ordinary English, which turned out to constrain vocabulary and say nothing at all about length. It was satisfied for a long time by long clause-chained sentences built out of short words. A rule about the shape of a sentence is refusable in a way an adjective is not.

## Cut what changes nothing

A detail that changes nothing the reader would do is cut, table or not. A word budget was tried and dropped, because length was never the defect and density is. A cap punishes writing that genuinely needs the words and invites padding what does not.

## Tables and bullets

Tables are allowed where a table genuinely reads better than a paragraph: a name-to-name rename mapping, or two measured columns being compared. Bullets are allowed only when enumerating a list of things. Do not use bullets to break up an argument — an argument is prose.

## Showing a change

A change is shown to the reader rather than described to them. What a command printed does not reach them: the output of a tool call goes to the session and not into the conversation, so a diff read out of a tool result is a diff nobody has seen. Put it in the reply itself, inside a fenced `diff` block, which the terminal colours red and green the way git does.

Quoting the old and new text as block quotes instead was tried three times in one session and failed three times. It loses the colouring, loses the alignment that puts a changed line against the line it replaced, and takes more room to say less. Where a hunk carries long unchanged lines, cut them and say what the marker stands for, so the elision is not read as a deletion.

## Related notes

Nothing here is hard-wrapped — see [markdown-is-not-hard-wrapped](markdown-is-not-hard-wrapped.md). How these rules land on the six sections of an issue, and which section carries the identifiers, is in [how-issues-are-written](how-issues-are-written.md).
