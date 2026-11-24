# The lab's product, process and resource AASs

aas-model's types and submodels for the AASs of the lab's modules, products and processes, beside
the stations (`resource_template.stations`, `resource_instances`). The split follows ISA-88's recipe
levels:

| AAS | ISA-88 | One per | Says | Type |
| --- | --- | --- | --- | --- |
| Product | General recipe | product, and each part with a recipe of its own | what the product is, the processes it needs and the capabilities they require, its recipe; no equipment | `aas_model.product_template.Product` |
| Process | Master recipe | product and line | the recipe bound to one line: per step the resource, the skill and its inputs; whether it fits | `aas_model.process_template.Process` |
| Resource | (equipment) | line, module, component | what it offers and how it is called, what its skills are made of, its live values and where it is | `aas_model.resource_template.modules`: `ProductionSystem`, `Module`, `Component` |

Why three: a reconfiguration of a line changes the resources and at most the process AAS, never the
product; one product on two lines is two process AASs and one product AAS; the product designer, the
line engineer and the vendor each own one AAS.

The resource types follow the resource ontology ARSO (`https://w3id.org/2025/arso`), which
iec61499-mgmt-py keeps (`ontology/ARSO`); the instances of the lab's reference line are built there
too (`cell/examples/example_line.py`).

## The types and their submodels

| Type | Asset kind, asset type | Submodels |
| --- | --- | --- |
| `Module` | Instance, `.../Resource/Module` | Nameplate, Hierarchical Structures (its components), Asset Interfaces Description (one OPC UA server), Asset Interfaces Mapping Configuration, [Skills](lab-submodels/Skills.md), [Variables](#variables-and-coordinates), Capability Description (offered; optional); optional [Control Configuration](lab-submodels/ControlConfiguration.md) and [Parameters](lab-submodels/Parameters.md) |
| `Component` | Instance, `.../Resource/Component/<Kind>` | [Skills](lab-submodels/Skills.md): its primitives, which its module carries out |
| `ProductionSystem` | Instance, `.../Resource/System` | Hierarchical Structures (its modules, each by its asset id); optional [Variables](#variables-and-coordinates) with the coordinates of its own points |
| `Product` | Type, `.../Product` | Nameplate, Hierarchical Structures (its bill of material; a part states its `Quantity` and `QuantityUnit`), [Process Parameters](lab-submodels/ProcessParameters.md), Capability Description (required), [Production Sequence](lab-submodels/ProductionSequence.md); optional State Declaration (the state of its units: asserted, observed or derived, D36) |
| `Batch` | Instance, `.../Batch` | Batch Information (the product type AAS, the quantity), Goal (Subjects and a condition tree every unit is to reach; the planner reads it, D13). Units are not listed: each BT instance mints the IRI of the unit it makes (`urn:uuid:<uuid>`, D10, D35), whose uuid the stations queue |
| `Process` | Type, `.../Process` | [Process Information](lab-submodels/ProcessInformation.md), [Bindings](lab-submodels/Bindings.md), [Validation](lab-submodels/Validation.md) |

`Module`, `Component` and `ProductionSystem` are `Resource`s (through `ArsoResource`); a submodel of
`Resource` a kind does not have is left out (`None`). What changes from IDTA's templates
(`resource_template/modules/submodels.py`):

- **Capability Description (IDTA 02020):** the lab's extension, shared with the stations
  (`submodel_templates.capability_description`): a capability is realized by a skill of the same AAS or a
  component's (`RealizedBySkill`, a model reference where IDTA leaves an external one); a property is
  the variable of the module it is (`SameAs`); a property constraint is a `BasicConstraint` expression. A
  property may list the values a module takes (IDTA's `SubmodelElementList` kind: the containers vial,
  syringe, cartridge). The ConstraintSet is otherwise as IDTA has it; the lab does not use it to say what a
  capability needs and changes. That is in the CapabilityRelations (`submodel_templates.execution`), which the
  planners and the behaviour tree read and the DMP does not:
  - **Subjects:** who takes part, an ordered list (SML) of ReferenceElements, each with a display name
    ("Container in the nest"); a term references a subject by its index. Its value is the AAS it is (Self, a component), or an external reference to the semantic id of what it stands
    for where it is only known at run time (a unit: the products' asset type; a place: a coordinate; a requirement
    of the unit's product, `RequirementSubject`: the meaning of the required property). Who a run-time subject is,
    the behaviour tree binds: a unit is the IRI its tree instance minted (`urn:uuid:<uuid>`), a requirement the
    element of the batch's product type with that meaning. The planar shuttle's move has the
    subjects "This shuttle" and "Target place" and ends with the shuttle at that place; a module's Occupying needs a
    shuttle at its transfer point holding the unit, and moves custody (`HeldBy`) to the module, which Filling needs.
  - **ConditionSet:** what must hold of the subjects, Pre (at the start), Invariant (throughout) and Post (at
    the end).
  - **EffectSet:** what changes, Start, During (definitions while it runs) and End.
  - **Translation** (D34): two Lua scripts the behaviour tree runs around the call. `Call` builds the realizing
    Operation's inputs from the subjects and the capability's properties (the unit's uuid for a station's command,
    the volume the product requires, the place's projected pose); `Reply` reads its outputs and says whether the
    action succeeded and which outcome of a OneOf happened (Filling's weight against the product's required
    FillWeight), or which of the skill's Errors it failed with. Neither writes state: the tree applies the declared
    effects of that outcome. A capability the tree runs is realized by exactly one skill, whose Operation holds only
    what the device's action takes and answers; the DMP maps it to the action and back and reads nothing else. A
    parameter with the `AcceptsReference` qualifier may be sent as a ReferenceElement under its own idShort, which
    the DMP resolves at the call (D27).

  Each holds trees of terms whose kind is their semantic id (Condition, Effect, And, Or, Not, Exists,
  ForAll, When, OneOf), nesting freely; a Condition or Effect names its Subject, and the property as a
  supplemental semantic id. A term's idShort (`Term_00`) only orders it; its display name says what it states.
  A **Duration** (a nominal value, or a formula over the capability's properties and the call's parameters) says
  how long the action takes where no Rate of an End effect does. Whether a state property has one value or a
  set, and its kind of value, is its meaning's: `lab:cardinality` and `lab:valueType`, proposed for the lab
  vocabulary in `vocabulary/lab-execution.ttl` (with `Location`, `Occupying`, `FillResult`); every state
  property the example line uses has both (`tests/test_vocabulary.py`). They are what the planners, the behaviour tree and the DMP read.
- **Asset Interfaces Description:** one OPC UA interface (`ModuleInterfaces`).
- **Hierarchical Structures:** parts that have parts in turn (`LocatedNode`). Where a part is, is a
  coordinate, not a statement of the node.
- **Nameplate:** the lab's (`LabNameplate`), for each instance to state its own values in.

## Submodels that are the lab's own

| Submodel | Semantic id | Template | Classes | Description |
| --- | --- | --- | --- | --- |
| Skills | `https://smartproductionlab.aau.dk/ARSO/Skills/1/0/Submodel` | `templates/arso/Skills.json` | `submodel_templates.arso.skills` | [Skills](lab-submodels/Skills.md) |
| Parameters | `https://smartproductionlab.aau.dk/ARSO/Parameters/1/0/Submodel` | `templates/arso/Parameters.json` | `submodel_templates.arso.parameters` | [Parameters](lab-submodels/Parameters.md) |
| Control Configuration | `https://smartproductionlab.aau.dk/ARSO/ControlConfiguration/1/0/Submodel` | `templates/arso/ControlConfiguration.json` | `submodel_templates.arso.control_configuration` | [Control Configuration](lab-submodels/ControlConfiguration.md) |
| Process Parameters (IDTA 02031-1, extended) | `https://admin-shell-io/idta/SubmodelTemplate/ProcessParameters/1/0` | `templates/product/ProcessParameters.json` | `submodel_templates.product.process_parameters` | [Process Parameters](lab-submodels/ProcessParameters.md) |
| Production Sequence | `https://smartproductionlab.aau.dk/SubmodelTemplate/ProductionSequence/2/0` | `templates/product/ProductionSequence.json` | `submodel_templates.product.production_sequence` | [Production Sequence](lab-submodels/ProductionSequence.md) |
| Process Information | `https://smartproductionlab.aau.dk/ProcessInformation/1/0/Submodel` | `templates/process/ProcessInformation.json` | `submodel_templates.process.process_information` | [Process Information](lab-submodels/ProcessInformation.md) |
| Bindings | `https://smartproductionlab.aau.dk/ProcessBindings/1/0/Submodel` | `templates/process/Bindings.json` | `submodel_templates.process.bindings` | [Bindings](lab-submodels/Bindings.md) |
| Validation | `https://smartproductionlab.aau.dk/ProcessValidation/1/0/Submodel` | `templates/process/Validation.json` | `submodel_templates.process.validation` | [Validation](lab-submodels/Validation.md) |
| State Declaration | `https://smartproductionlab.aau.dk/submodels/StateDeclaration/1/0` | none (hand-written classes) | `submodel_templates.state_declaration` | the state variables of a subject (asserted, written by the behaviour tree; observed, a linked projection: an AIMC mapping of the same AAS sinks into it, as into a time-series segment, its Lua converting the reported value where needed, as a station's process queue into `OccupiedBy`; derived, computed by query), its initial values and the store they are kept in |
| Variables, with Coordinates | `https://smartproductionlab.aau.dk/submodels/Variables/1/0` | none (hand-written classes) | `submodel_templates.variables`, `submodel_templates.coordinates` | [below](#variables-and-coordinates) |

**How they are made:**

```
ontology ARSO --modreg generate (iec61499-mgmt-py)--> templates/arso/*.json
templates/{arso,product,process}/*.json --scripts/lab_generate.py--> submodel_templates/{arso,product,process}/*.py
templates/... + docs/lab-submodels/*.md --scripts/lab_docs.py--> the element tables of the descriptions
```

The templates of the product and the process are kept as files: the planner's Production Sequence,
IDTA 02031-1 with the lab's extension, and the process AAS's three (written by hand until the process
ontology is remade). `tests/test_lab_templates.py` fails when the classes or the descriptions are not
those of the templates.

**Class names:** aas_pydantic reads an element back as the class its dump names, among all classes
of the package. A generated class named like another one with other fields gets a name of its own
(`lab_generate.RENAMED`, `READABLE`): `FlowCondition`, `ProcessStepBinding`, `InputBinding`,
`ProcessParameterGroup`; the product's part is a `ProductPart`; the coordinates' classes are `RelativeCoordinate`, `CoordinateX`, ...

## Variables and Coordinates

A module's values and where it is: aas-model's `Variables` submodel
(`submodel_templates/variables.py`), used by the stations and the modules alike. The lab's modules
keep no live value in the AAS: their values are fields of time series (`State/Module`,
`State/<Skill>`, `State/Procedures`, `Measurements/<Item>`), whose rows a mapping writes to the
time series database and whose segment says where they are; a reader asks the database for the
latest value or a span.

```
Variables
├── State                         time series of discrete status (PackML state, occupation)
├── Measurements                  time series of measured values; a value that is not a series is a
│                                 VariableProp in its group (its meaning a supplemental semantic id); and:
│   └── Coordinates               where the asset and its points are
│       └── {coordinate}          RelativeCoordinate; its meaning a supplemental semantic id
│           ├── RelativeTo        the coordinate it is relative to, in this AAS or another
│           ├── X, Y, Z           mm, along the parent's axes          (IDTA 02075 x/y/zframe)
│           ├── Roll, Pitch, Yaw  degrees, about the parent's fixed X, then Y, then Z axis
│           └── {value}Source     the variable a moving value is (ZSource)
└── Log                           time series of what is logged (skill calls)
```

| Element | Class | Semantic id |
| --- | --- | --- |
| `Measurements/Coordinates` | `Coordinates` | `https://smartproductionlab.aau.dk/variables/Coordinates/1/0` |
| `.../{coordinate}` | `RelativeCoordinate` | `https://smartproductionlab.aau.dk/variables/Coordinate/1/0` |
| `.../{coordinate}/RelativeTo` | `CoordinateRelativeTo` | `https://smartproductionlab.aau.dk/variables/Coordinate/RelativeTo/1/0` |
| `.../{coordinate}/X`, `Y`, `Z` | `CoordinateX`, `CoordinateY`, `CoordinateZ` | `https://admin-shell.io/idta/cds/xframe/1`, `yframe`, `zframe` (xs:double, mm) |
| `.../{coordinate}/Roll`, `Pitch`, `Yaw` | `CoordinateRoll`, `CoordinatePitch`, `CoordinateYaw` | `https://admin-shell.io/idta/cds/rxframe/1`, `ryframe`, `rzframe` (xs:double, deg) |
| `.../{coordinate}/{value}Source` | `CoordinateSource` | `https://smartproductionlab.aau.dk/variables/Coordinate/Source/1/0` |

- **A tree of transforms across AASs,** rooted at one coordinate without `RelativeTo` (in the lab, the
  planar table's base): a module's base is relative to it, the module's points and mounts to its
  base, an end effector to its mount, a shuttle to the table's base, a product to the shuttle it
  rides. Where a point is in the root's frame is composed along the references (R = Rz(Yaw)
  Ry(Pitch) Rx(Roll), as ROS's RPY), never stored.
- **Measurements,** because the modules will report where they are themselves (RFID): even a fixed
  pose is measured.
- **A part that moves is two coordinates:** a fixed mount, and the moving part relative to it, whose
  moving values are each one variable (`ZSource`). A record of its history is then that variable's.
- **Meanings** come from the lab's vocabulary (`https://smartproductionlab.aau.dk/semantics/...`):
  TableBase, ModuleBase, Mount, EndEffector, Mover, Flyway, TransferPoint, ProcessingPoint,
  PickPoint, PlacePoint.

## Authoring and building

Write an instance with the classes, element by element, and build the AAS:

```python
from aas_model import Product, build_from_model
from aas_model.submodel_templates.product import production_sequence as ps

vial = Product(id_short="Vial2mLAAS", id="https://smartproductionlab.aau.dk/aas/Vial2mLAAS",
               production_sequence=ps.ProductionSequence(...))
store = build_from_model(vial)          # a BaSyx object store: the shell and its submodels
```

Two of them are written out here too, with the execution model: the filling module and its three components
(`aas_model.resource_instances.modules`: each component offers its capability in its own AAS, in
`AuxiliaryCapabilities`; the module states what holds of each in this station, a specialization of the
component's (GeneralizedBy across the AASs), and the offered Filling derived from them) the 2 mL vial (`aas_model.product_instances`, with the State Declaration
of its units) and a batch of three of them with its goal (`aas_model.batch_instances`); `tests/test_example_line.py` builds them as one line and resolves every reference across them. Their AAS JSON is checked in under `examples/aas/`
(`scripts/export_examples.py`).

The lab's reference instances, written out in full, are in iec61499-mgmt-py: the products
(`cell/examples/products`), the processes (`cell/examples/processes`), and the modules, the line, the
planar table and its shuttles built from their specs by `modreg` (`cell/examples/example_line.py`,
which writes every AAS and can publish them to an AAS server).
