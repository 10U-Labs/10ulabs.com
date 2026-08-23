# Prose leads with the concept

## Table of Contents

- [Who the reader is](#who-the-reader-is)
- [Lead with what the thing is for](#lead-with-what-the-thing-is-for)
- [Concepts rather than identifiers](#concepts-rather-than-identifiers)
- [No jargon where a plain word will do](#no-jargon-where-a-plain-word-will-do)
- [One idea to a sentence](#one-idea-to-a-sentence)
- [Cut what changes nothing](#cut-what-changes-nothing)
- [Tables and bullets](#tables-and-bullets)
- [Related notes](#related-notes)

## Who the reader is

Everything written here is read by somebody who was not in the conversation that produced it and does not have the files open. That covers an issue, a commit message, a comment on an issue and a reply in the session. Write for that reader.

## Lead with what the thing is for

Lead with what the thing is for. A paragraph opens by saying what the thing is and what it does, before any file, function or line is named. Say what a defect costs in ordinary words near the top rather than in the seventh paragraph. Opening with the concept is not a licence to re-establish context the reader already has; leading and restating are different things.

## Concepts rather than identifiers

Write in concepts, not identifiers. Say what the code does and what goes wrong in plain words, without hedging. An argument about behaviour that only holds while the reader is looking at the file is one the reader cannot check. Identifiers belong where the reader has stopped reading and started working: the change being proposed, the file to edit, the function to delete.

Writing in concepts is not writing in abstractions, and this is the way it goes wrong. Swapping a name for a compound noun makes a sentence vaguer rather than plainer, because a name at least points at something: "a cached-client package sits in the shared Python library" says less than the package's own name would have. The thing a piece of writing is about may be named, once, so the reader knows what is under discussion. What is barred is the supporting cast — the other files, the functions, the line numbers — and the way out of a sentence full of them is to explain the idea in ordinary words, not to replace each name with a category.

## No jargon where a plain word will do

Use a plain word wherever one exists. Jargon from computer science is not made acceptable by being accurate, and a reader who has to decode the first sentence has been handed the writer's job. Where a term genuinely has no plain equivalent, say what it means in passing the first time it appears.

A vague stand-in is not a plain word, and reaching for one is the second way this goes wrong. "A small helper object" is worse than the term it was avoiding, because it names nothing and still has to be decoded, and the reader now has to guess at what was too technical to say. Where the real word is the clearest one available, write it and explain it in the same sentence.

Repeat the noun rather than reaching back for it with a pronoun. A reader who has to search backwards to find what "it" or "one" stands for is doing the work the writer skipped, and the search gets harder with every clause in between. The word "one" is the worst of them, because it is a counter as well as a stand-in and a paragraph can easily use it as both: "a client, one per service" and then "asking for one is not free" put two different jobs on the same word two clauses apart.

## One idea to a sentence

One idea to a sentence. Do not chain subordinate clauses to fit a second idea in. This replaced an older rule that asked for simple, plain, ordinary English, which turned out to constrain vocabulary and say nothing at all about length. It was satisfied for a long time by long clause-chained sentences built out of short words. A rule about the shape of a sentence is refusable in a way an adjective is not.

## Cut what changes nothing

A detail that changes nothing the reader would do is cut, table or not. A word budget was tried and dropped, because length was never the defect and density is. A cap punishes writing that genuinely needs the words and invites padding what does not.

## Tables and bullets

Tables are allowed where a table genuinely reads better than a paragraph: a name-to-name rename mapping, or two measured columns being compared. Bullets are allowed only when enumerating a list of things. Do not use bullets to break up an argument — an argument is prose.

## Related notes

Nothing here is hard-wrapped — see [markdown-is-not-hard-wrapped](markdown-is-not-hard-wrapped.md). How these rules land on the six sections of an issue, and which section carries the identifiers, is in [how-issues-are-written](how-issues-are-written.md).
