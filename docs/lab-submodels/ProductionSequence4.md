# Production Sequence 4.0

A product's recipe as a partial order (proposed): the steps that put the product together
(Assembly) or take it apart (Disassembly), the order between them as relations (`ProcessOrder`, as in
APSO's bill of process), and the joints each step makes or breaks. It sits beside the planner's [Production Sequence](ProductionSequence.md) 2.0, which
the lab's products still use; the planner (basyx-aas-web-ui, module ProcessSequence) does not read
4.0 yet. In the product AAS (`aas_model.product_template.Product`: `assembly_sequence`,
`disassembly_sequence`).

Classes: `aas_model.submodel_templates.product.production_sequence_4` (generated).

## How it is used

- **One sequence per archetype at most.** `ArcheType` is Assembly or Disassembly. The submodel's id
  is the product's plan id with the archetype after it (`aas_model.product_template.sequence_id`), its
  idShort `ProductionSequenceAssembly` or `ProductionSequenceDisassembly`. `Product` checks that each
  field holds a sequence of its archetype.
- **A partial block** (Kind `partial`) holds steps in `Steps` that run in any order its
  `ProcessOrders` allow. Each `ProcessOrder` is a relation between two steps of the block: `first`
  must be done before `second` starts. Its annotation `Reason` may say why (a joint in the way,
  access, an order fixed by GMP). A step that no relation has as `second` is ready when the block
  starts. `Order` stays: an order that respects the relations, which a reader that runs steps one by
  one follows.
- **A step's `EstimatedDuration`** (seconds) is what a scheduler plans with; the examples' values are
  made up.
- **A joint** is an AnnotatedRelationshipElement in the `Joints` of the step that makes it
  (Assembly) or breaks it (Disassembly). `first` and `second` are entities of the Hierarchical
  Structures of the AAS that holds the step. `JointType` and `JointStandard` are its annotations; the
  kind of joint is also its supplemental semantic id (`https://smartproductionlab.aau.dk/semantics/ScrewedJoint`,
  `PlugJoint`, ...). The parameters of the joint (a torque, a force) are those of the step's process
  in Process Parameters. The other archetype's step refers to the joint (`JointReference`) instead of
  defining it again.
- **A step** (Kind `step`) refers to its process (`ProcessReference`). A **call** (Kind `call`) names a
  part of the bill of material (`Part`, an entity of the Hierarchical Structures), e.g. a subassembly
  with an AAS of its own; the sequence it runs is found through the part: its asset id, the part's AAS,
  that AAS's sequence of the same `ArcheType`. No reference from one sequence to another: the bill of
  material already says which AAS a part has. A
  **decision** (Kind `decision`) takes one of its two branches by comparing an output of a step done
  before (`Outputs`) with `Expected`.
- **The equipment is the process AAS's.** A step names no resource, skill or binding: the
  [Bindings](Bindings.md) of a process AAS bind each step to a resource and a skill, through its path
  (`Steps/Step_0000/Steps/Step_0001` for a step of a partial block).

## Why it is shaped so

- **A partial order instead of a list:** disassembly and assembly rarely have one order. What must
  come first is what is fixed; the agents and the planner choose among the steps that are ready.
- **The order as relations, between siblings only:** the colleagues' APSO states the order of a bill of
  process as `ProcessOrder` relations, and the relation can carry why the order holds. They stay
  inside the block, between its steps, so a block is a graph of its own that can be checked alone (no
  cycles, `Order` respects the relations), and a call or a nested block is one node of it. Until
  26 Nov 2026 the order was an `After` list on each step: the same edges, kept on the later step.
- **Joints in the sequence, not in the Hierarchical Structures:** the bill of material stays a list
  of parts. A joint is what a step does to two parts, so it is defined where the step is.
- **A call names the part, not its sequence:** until 26 Nov 2026 a call had `SequenceReference` (the
  called submodel) and `Component` (the part's asset id, its AAS): the same link as the bill of
  material's entity, stated twice. Now the entity is the one link.
- **What stays from 2.0 and 3.0:** the step kinds, `Order`, `ProcessReference`, calls, branches,
  conditions, a step's outputs and the decision on them. What is left out: `PlanSchema`, `SequenceId`,
  `Role`, `Subprocesses` and the equipment of a step (`Resource`, `SkillId`, `Skill`,
  `ExecutionMode`, `Bindings`).

## Example

In aas-model (`aas_model.product_instances`, built by `scripts/export_precedence_examples.py`):

- **The battery pack** (`battery_pack`): Disassembly, a partial block whose seven ProcessOrders say:
  UnscrewCover and UnplugHV are ready at the start; RemoveBusbars after both; RemoveBMS after UnplugHV;
  the four modules' own sequences called after RemoveBusbars. The joints J_Cover, J_HV, J_Busbar1-4 are defined here. Its
  Assembly sequence refers to the same joints.
- **A battery module** (`battery_module`): RemoveLid, TestCells (output StateOfHealth), then a
  decision: 80 % or more to SortForReuse, otherwise SortForRecycling.
- **The 2 mL vial** (`vial_2ml`): Assembly, a chain (Filling, Stoppering, Capping, Inspection) because
  GMP fixes the order; Stoppering makes the press fit J_Stopper, Capping the crimp J_Seal.

## Elements

<!-- The table below is written by scripts/lab_docs.py from the template; do not edit it. -->

**Submodel** `ProductionSequence`, semantic id `https://smartproductionlab.aau.dk/SubmodelTemplate/ProductionSequence/4/0`, version 4.0; template `templates/product/ProductionSequence4.json`.

| Element (path) | Kind | Card. | Semantic id | Description |
| --- | --- | --- | --- | --- |
| `ArcheType` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/ArcheType/1/0` | Assembly or Disassembly: what the sequence does with its subject. |
| `Revision` | Property (xs:nonNegativeInteger) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Revision/1/0` | Counts the saved changes of the sequence. |
| `Name` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | The name shown for the sequence. |
| `Subject` | Ref | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Subject/1/0` | The AAS of the product the sequence plans. |
| `Steps` | SMC | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0` | The nodes of the sequence. |
| `Steps/{Step}` | SMC | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/Step/1/0` | One node of the sequence. Kind step: a process of the product. Kind call: the sequence of a part of the bill of material. Kind partial: steps that run in any order their ProcessOrders allow. Kind parallel: branches that all join. Kind conditional: steps that only run when the condition holds. Kind decision: one of two branches, by the condition. |
| `Steps/{Step}/NodeId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/NodeId/1/0` | Identifies the node within its sequence. |
| `Steps/{Step}/Kind` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Kind/1/0` | step, call, partial, parallel, conditional or decision. |
| `Steps/{Step}/Name` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | The name shown for the node. |
| `Steps/{Step}/Order` | Property (xs:nonNegativeInteger) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Order/1/0` | Position among the nodes beside it. In a partial block, an order that respects its ProcessOrders: the default the steps run in. |
| `Steps/{Step}/EstimatedDuration` | Property (xs:double) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/EstimatedDuration/1/0` | Kind step: how long the step is expected to take, in seconds, for scheduling. |
| `Steps/{Step}/ProcessOwner` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/ProcessOwner/1/0` | Kind step: the AAS whose process the step runs, where it is not the Subject. |
| `Steps/{Step}/ProcessReference` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/ProcessReference/1/0` | Kind step: the process, in the owner's Process Parameters. |
| `Steps/{Step}/RequiredCapabilities` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/RequiredCapabilities/1/0` | Kind step: the capabilities the step requires, where they differ from those of its process. |
| `Steps/{Step}/RequiredCapabilities/{RequiredCapability}` | Ref | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/RequiredCapability/1/0` | A Required capability in a Capability Description. |
| `Steps/{Step}/Joints` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Joints/1/0` | Kind step: the joints the step makes (Assembly) or breaks (Disassembly). |
| `Steps/{Step}/Joints/{Joint}` | ARE | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/JointConnection/1/0` | A joint between two parts of the bill of material (first and second, entities of the Hierarchical Structures of the AAS that holds the step). What kind of joint it is, is also its supplemental semantic id. |
| `Steps/{Step}/Joints/{Joint}/JointType` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/JointType/1/0` | The kind of joint, as the joint tools name it: Screw, Plug, Bolt, Clip, PressFit, Crimp. |
| `Steps/{Step}/Joints/{Joint}/JointStandard` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/JointStandard/1/0` | The standard the joint is made to, e.g. DIN 8593-3. |
| `Steps/{Step}/Joints/{JointReference}` | Ref | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/JointReference/1/0` | A joint defined in the product's sequence of the other archetype. |
| `Steps/{Step}/Outputs` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Outputs/1/0` | Kind step: what the step reports when done, for a decision to compare. |
| `Steps/{Step}/Outputs/{Output}` | SMC | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/Output/1/0` | One value the step reports. |
| `Steps/{Step}/Outputs/{Output}/OutputId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/OutputId/1/0` | Identifies the output within its step. |
| `Steps/{Step}/Outputs/{Output}/Name` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | The name shown for the output. |
| `Steps/{Step}/Outputs/{Output}/DataType` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/DataType/1/0` | The type of the value, e.g. xs:double, xs:boolean. |
| `Steps/{Step}/Outputs/{Output}/Unit` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Unit/1/0` | The unit of the value. |
| `Steps/{Step}/Part` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Part/1/0` | Kind call: the part whose own sequence is run, an entity of the Hierarchical Structures of the AAS that holds the step. Its asset id leads to the part's AAS; the sequence run is that AAS's sequence of the same ArcheType. |
| `Steps/{Step}/OccurrenceId` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/OccurrenceId/1/0` | Kind call: identifies this use of the part, where the bill of material holds it more than once (a Quantity above 1). |
| `Steps/{Step}/Condition` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Condition/1/0` | Kind conditional and decision: when the guarded steps run, or which branch is taken. |
| `Steps/{Step}/Condition/ConditionType` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/ConditionType/1/0` | everyNthProduct, or comparison (an output against Expected). |
| `Steps/{Step}/Condition/EveryNProducts` | Property (xs:positiveInteger) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/EveryNProducts/1/0` | everyNthProduct: every how many products. |
| `Steps/{Step}/Condition/CounterScope` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/CounterScope/1/0` | everyNthProduct: what the count runs over, e.g. productionRun. |
| `Steps/{Step}/Condition/Operator` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Operator/1/0` | comparison: lessThan, lessOrEqual, equal, greaterOrEqual, greaterThan. |
| `Steps/{Step}/Condition/Unit` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Unit/1/0` | comparison: the unit of Expected. |
| `Steps/{Step}/Condition/Expected` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Expected/1/0` | comparison: the value the output is compared with. |
| `Steps/{Step}/Condition/Expected/DataType` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/DataType/1/0` | The type of the value. |
| `Steps/{Step}/Condition/Expected/Value` | Property (xs:double) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Value/1/0` | The value. |
| `Steps/{Step}/Condition/Operand` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Operand/1/0` | comparison: the output compared. |
| `Steps/{Step}/Condition/Operand/OperandType` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/OperandType/1/0` | output: the output of a step done before. |
| `Steps/{Step}/Condition/Operand/StepId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/StepId/1/0` | The NodeId of the step. |
| `Steps/{Step}/Condition/Operand/OutputId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/OutputId/1/0` | The OutputId of its output. |
| `Steps/{Step}/Steps` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0` | Kind partial and conditional: the steps inside, each a Step as described here. |
| `Steps/{Step}/ProcessOrders` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/ProcessOrders/1/0` | Kind partial: the order of the steps inside, one relation for each pair that must keep its order. A step that no relation has as second is ready when the block starts. |
| `Steps/{Step}/ProcessOrders/{ProcessOrder}` | ARE | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/ProcessOrder/1/0` | first must be done before second starts. Both are steps of this block (their collections in its Steps). |
| `Steps/{Step}/ProcessOrders/{ProcessOrder}/Reason` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Reason/1/0` | Why the order holds, e.g. a joint in the way, access, an order fixed by GMP. |
| `Steps/{Step}/Branches` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Branches/1/0` | Kind parallel and decision: the branches. A decision has two: Order 0 when the condition holds, Order 1 when not. |
| `Steps/{Step}/Branches/{Branch}` | SMC | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/Branch/1/0` | One branch. |
| `Steps/{Step}/Branches/{Branch}/BranchId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/BranchId/1/0` | Identifies the branch. |
| `Steps/{Step}/Branches/{Branch}/Name` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | The name shown for the branch. |
| `Steps/{Step}/Branches/{Branch}/Order` | Property (xs:nonNegativeInteger) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Order/1/0` | Position among the branches. |
| `Steps/{Step}/Branches/{Branch}/Steps` | SMC | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0` | The steps of the branch, each a Step as described here. |
