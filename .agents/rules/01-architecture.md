# DealFlow360 Architecture Rule

- Follow the modular-monolith structure in `docs/specs/DealFlow360_Backend_Folder_Structure.txt`.
- Keep routers thin; business workflows belong in services.
- Put complex reusable calculations in engines.
- Put persistence/query logic in repositories.
- Keep SQLAlchemy models free of business workflows.
- Use transaction boundaries for multi-record business operations.
- Do not introduce infrastructure outside the finalized stack.
- Do not add tables omitted by the finalized schema without explicit approval.
- Preserve quotation as the central sales aggregate and quotation_lines as the commercial source for orders.
