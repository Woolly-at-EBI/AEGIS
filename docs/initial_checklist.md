```mermaid
flowchart TD
    A[MInAs] -->mapping(initial mapping)
    AEGIS --> mapping
    ENA_checklist --> mapping
    mapping --"in person discussion"--> mapping
    mapping --> mapping_imp(improved mapping)
    AEGIS_IMP(AEGIS term details)--> mapping_imp
    mapping_imp -- "  "--> prot_checklist(prototype aDNA checklist)
```
