---
name: efficient-coding
description: Solve software engineering tasks with targeted repository exploration and less unnecessary context, repeated reading, and redundant tool use. Use when implementing, debugging, or modifying code in a repository while preserving correctness.
---

# Efficient Coding

Optimize for correctness first and resource efficiency second.

## 1. Start with a hypothesis

Before broad repository exploration:

- Identify the requested behavior and success criteria.
- Infer the most likely files, symbols, or subsystem involved.
- Start from those hypotheses instead of scanning the repository broadly.

## 2. Explore narrowly

Prefer targeted searches for filenames, symbols, references, imports, error messages, and nearby tests.

Read the smallest useful set of files first.

Do not recursively inspect large directories or unrelated files unless evidence shows they are relevant.

## 3. Expand only with evidence

Expand exploration when the current information cannot answer a specific question or when tests, dependencies, callers, configuration, or runtime behavior indicate that more context is required.

Do not gather context speculatively.

## 4. Avoid repeated work

Reuse information already gathered during the task.

Do not reread unchanged files, repeat equivalent searches, or rerun unchanged commands unless verification or new evidence requires it.

## 5. Validate progressively

Run the smallest relevant test or validation first.

Broaden validation only after the focused change works or when integration risk requires it.

## 6. Preserve correctness

Never skip necessary investigation, implementation, or validation merely to reduce tokens or tool calls.

Efficiency means eliminating unnecessary work, not incomplete work.
