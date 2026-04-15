# Compiler Toolkit

An opinionated library to help you build compilers.

# Features

- [x] Ast Creation Tools
- [x] Ast Walk functionality built in
- [x] Ast node typing garauntees (ensure that all nodes are well defined)
- [x] Ast nodes having configurable parser patterns (WIP, needs to be more ergonomic)
- [x] Utility decorators for annotation of individual parts of the compilers
- [x] Parser pattern builder
  - [ ] unions on patterns (`or` clause)
  - [ ] `and` clause on patterns
- [x] Parser builder (WIP, needs to be more ergonomic)
- [ ] Parser check functions built into patterns to allow automatic syntax error parsing.
- [ ] Source error highlighting (fine grained highlights)
- [x] Package and module tree utilities
- [x] Lexing via rply library (and utilities)
- [x] Parser token class builtin

# What this does not provide

- This will not do codegen
- This will not give you lexing capabilities outside of making the use of rply's lexer generator more ergonomic
- This will not provide a type system
- This will not teach you how to build a compiler (altho it will certainly aid in the creation of your first one!)
