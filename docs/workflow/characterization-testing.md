# Characterization Testing

Characterization tests capture what the system currently does.

Use them before refactoring legacy or unclear behavior. They create a safety net for changing structure without accidentally changing externally observable behavior.

Characterization tests may capture awkward or undesirable behavior. That is acceptable when the goal is to preserve behavior during a refactor. If the behavior should change, write or update a spec first and then write intended behavior tests for the new contract.

Good characterization tests:

- target observable behavior at boundaries such as HTTP responses, forms, models, management commands, database side effects, emitted messages, files, or external service calls
- avoid private methods and internal call order unless those details are part of an explicit contract
- mock external systems only at the boundary
- are labeled clearly as characterization tests
- document surprising or undesirable behavior they capture

Characterization tests are not a substitute for intended behavior tests. Promote or replace them when a better functional spec exists.
