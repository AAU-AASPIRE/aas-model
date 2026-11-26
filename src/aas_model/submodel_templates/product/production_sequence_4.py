"""ProductionSequence - generated from IDTA template.
Source: templates/product/ProductionSequence4.json
"""

from __future__ import annotations

from typing import Any, ClassVar, List, Dict, Optional, Union, TypeAlias
from aas_pydantic import (
    AnnotatedRelationshipElement, Property, ReferenceElement, Submodel, SubmodelElement, SubmodelElementCollection, SubmodelElementList,
)
from aas_pydantic.aas_model import AasIdString

class ArcheType(Property):
    id_short: AasIdString = "ArcheType"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/ArcheType/1/0"
    description: str = "Assembly or Disassembly: what the sequence does with its subject."
    value_type: str = "xs:string"

class Revision(Property):
    id_short: AasIdString = "Revision"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Revision/1/0"
    description: str = "Counts the saved changes of the sequence."
    value_type: str = "xs:nonNegativeInteger"

class Name(Property):
    id_short: AasIdString = "Name"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0"
    description: str = "The name shown for the sequence."
    value_type: str = "xs:string"

class Subject(ReferenceElement):
    id_short: AasIdString = "Subject"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Subject/1/0"
    description: str = "The AAS of the product the sequence plans."

class NodeId(Property):
    id_short: AasIdString = "NodeId"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/NodeId/1/0"
    description: str = "Identifies the node within its sequence."
    value_type: str = "xs:string"

class Kind(Property):
    id_short: AasIdString = "Kind"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Kind/1/0"
    description: str = "step, call, partial, parallel, conditional or decision."
    value_type: str = "xs:string"

class StepName(Property):
    id_short: AasIdString = "Name"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0"
    description: str = "The name shown for the node."
    value_type: str = "xs:string"

class Order(Property):
    id_short: AasIdString = "Order"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Order/1/0"
    description: str = "Position among the nodes beside it. In a partial block, an order that respects its ProcessOrders: the default the steps run in."
    value_type: str = "xs:nonNegativeInteger"

class EstimatedDuration(Property):
    id_short: AasIdString = "EstimatedDuration"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/EstimatedDuration/1/0"
    description: str = "Kind step: how long the step is expected to take, in seconds, for scheduling."
    value_type: str = "xs:double"

class ProcessOwner(ReferenceElement):
    id_short: AasIdString = "ProcessOwner"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/ProcessOwner/1/0"
    description: str = "Kind step: the AAS whose process the step runs, where it is not the Subject."

class ProcessReference(ReferenceElement):
    id_short: AasIdString = "ProcessReference"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/ProcessReference/1/0"
    description: str = "Kind step: the process, in the owner's Process Parameters."

class RequiredCapability(ReferenceElement):
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/RequiredCapability/1/0"
    description: str = "A Required capability in a Capability Description."

class RequiredCapabilities(SubmodelElementCollection):
    id_short: AasIdString = "RequiredCapabilities"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/RequiredCapabilities/1/0"
    description: str = "Kind step: the capabilities the step requires, where they differ from those of its process."
    RequiredCapability: Dict[str, RequiredCapability_t] = {}

class JointType(Property):
    id_short: AasIdString = "JointType"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/JointType/1/0"
    description: str = "The kind of joint, as the joint tools name it: Screw, Plug, Bolt, Clip, PressFit, Crimp."
    value_type: str = "xs:string"

class JointStandard(Property):
    id_short: AasIdString = "JointStandard"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/JointStandard/1/0"
    description: str = "The standard the joint is made to, e.g. DIN 8593-3."
    value_type: str = "xs:string"

class Joint(AnnotatedRelationshipElement):
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/JointConnection/1/0"
    description: str = "A joint between two parts of the bill of material (first and second, entities of the Hierarchical Structures of the AAS that holds the step). What kind of joint it is, is also its supplemental semantic id."
    JointType: JointType_t
    JointStandard: Optional[JointStandard_t] = None

class JointReference(ReferenceElement):
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/JointReference/1/0"
    description: str = "A joint defined in the product's sequence of the other archetype."

class Joints(SubmodelElementCollection):
    id_short: AasIdString = "Joints"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Joints/1/0"
    description: str = "Kind step: the joints the step makes (Assembly) or breaks (Disassembly)."
    Joint: Dict[str, Joint_t] = {}
    JointReference: Dict[str, JointReference_t] = {}

class OutputId(Property):
    id_short: AasIdString = "OutputId"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/OutputId/1/0"
    description: str = "Identifies the output within its step."
    value_type: str = "xs:string"

class OutputName(Property):
    id_short: AasIdString = "Name"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0"
    description: str = "The name shown for the output."
    value_type: str = "xs:string"

class DataType(Property):
    id_short: AasIdString = "DataType"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/DataType/1/0"
    description: str = "The type of the value, e.g. xs:double, xs:boolean."
    value_type: str = "xs:string"

class Unit(Property):
    id_short: AasIdString = "Unit"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Unit/1/0"
    description: str = "The unit of the value."
    value_type: str = "xs:string"

class Output(SubmodelElementCollection):
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Output/1/0"
    description: str = "One value the step reports."
    OutputId: OutputId_t
    Name: Union[OutputName, Name]
    DataType: DataType_t
    Unit: Optional[Unit_t] = None

class Outputs(SubmodelElementCollection):
    id_short: AasIdString = "Outputs"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Outputs/1/0"
    description: str = "Kind step: what the step reports when done, for a decision to compare."
    Output: Dict[str, Output_t] = {}

class Part(ReferenceElement):
    id_short: AasIdString = "Part"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Part/1/0"
    description: str = "Kind call: the part whose own sequence is run, an entity of the Hierarchical Structures of the AAS that holds the step. Its asset id leads to the part's AAS; the sequence run is that AAS's sequence of the same ArcheType."

class OccurrenceId(Property):
    id_short: AasIdString = "OccurrenceId"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/OccurrenceId/1/0"
    description: str = "Kind call: identifies this use of the part, where the bill of material holds it more than once (a Quantity above 1)."
    value_type: str = "xs:string"

class ConditionType(Property):
    id_short: AasIdString = "ConditionType"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/ConditionType/1/0"
    description: str = "everyNthProduct, or comparison (an output against Expected)."
    value_type: str = "xs:string"

class EveryNProducts(Property):
    id_short: AasIdString = "EveryNProducts"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/EveryNProducts/1/0"
    description: str = "everyNthProduct: every how many products."
    value_type: str = "xs:positiveInteger"

class CounterScope(Property):
    id_short: AasIdString = "CounterScope"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/CounterScope/1/0"
    description: str = "everyNthProduct: what the count runs over, e.g. productionRun."
    value_type: str = "xs:string"

class Operator(Property):
    id_short: AasIdString = "Operator"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Operator/1/0"
    description: str = "comparison: lessThan, lessOrEqual, equal, greaterOrEqual, greaterThan."
    value_type: str = "xs:string"

class ConditionUnit(Property):
    id_short: AasIdString = "Unit"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Unit/1/0"
    description: str = "comparison: the unit of Expected."
    value_type: str = "xs:string"

class ExpectedDataType(Property):
    id_short: AasIdString = "DataType"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/DataType/1/0"
    description: str = "The type of the value."
    value_type: str = "xs:string"

class Value(Property):
    id_short: AasIdString = "Value"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Value/1/0"
    description: str = "The value."
    value_type: str = "xs:double"

class Expected(SubmodelElementCollection):
    id_short: AasIdString = "Expected"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Expected/1/0"
    description: str = "comparison: the value the output is compared with."
    DataType: Union[ExpectedDataType, DataType]
    Value: Value_t

class OperandType(Property):
    id_short: AasIdString = "OperandType"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/OperandType/1/0"
    description: str = "output: the output of a step done before."
    value_type: str = "xs:string"

class StepId(Property):
    id_short: AasIdString = "StepId"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/StepId/1/0"
    description: str = "The NodeId of the step."
    value_type: str = "xs:string"

class OperandOutputId(Property):
    id_short: AasIdString = "OutputId"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/OutputId/1/0"
    description: str = "The OutputId of its output."
    value_type: str = "xs:string"

class Operand(SubmodelElementCollection):
    id_short: AasIdString = "Operand"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Operand/1/0"
    description: str = "comparison: the output compared."
    OperandType: OperandType_t
    StepId: StepId_t
    OutputId: Union[OperandOutputId, OutputId]

class Condition(SubmodelElementCollection):
    id_short: AasIdString = "Condition"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Condition/1/0"
    description: str = "Kind conditional and decision: when the guarded steps run, or which branch is taken."
    ConditionType: ConditionType_t
    EveryNProducts: Optional[EveryNProducts_t] = None
    CounterScope: Optional[CounterScope_t] = None
    Operator: Optional[Operator_t] = None
    Unit: Optional[Union[ConditionUnit, Unit]] = None
    Expected: Optional[Expected_t] = None
    Operand: Optional[Operand_t] = None

class Reason(Property):
    id_short: AasIdString = "Reason"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Reason/1/0"
    description: str = "Why the order holds, e.g. a joint in the way, access, an order fixed by GMP."
    value_type: str = "xs:string"

class ProcessOrder(AnnotatedRelationshipElement):
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/ProcessOrder/1/0"
    description: str = "first must be done before second starts. Both are steps of this block (their collections in its Steps)."
    Reason: Optional[Reason_t] = None

class ProcessOrders(SubmodelElementCollection):
    id_short: AasIdString = "ProcessOrders"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/ProcessOrders/1/0"
    description: str = "Kind partial: the order of the steps inside, one relation for each pair that must keep its order. A step that no relation has as second is ready when the block starts."
    ProcessOrder: Dict[str, ProcessOrder_t] = {}

class BranchId(Property):
    id_short: AasIdString = "BranchId"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/BranchId/1/0"
    description: str = "Identifies the branch."
    value_type: str = "xs:string"

class BranchName(Property):
    id_short: AasIdString = "Name"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0"
    description: str = "The name shown for the branch."
    value_type: str = "xs:string"

class BranchOrder(Property):
    id_short: AasIdString = "Order"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Order/1/0"
    description: str = "Position among the branches."
    value_type: str = "xs:nonNegativeInteger"

class Branch(SubmodelElementCollection):
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Branch/1/0"
    description: str = "One branch."
    BranchId: BranchId_t
    Name: Union[BranchName, Name]
    Order: Union[BranchOrder, Order]
    Steps: Optional[Steps_t] = None

class Branches(SubmodelElementCollection):
    id_short: AasIdString = "Branches"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Branches/1/0"
    description: str = "Kind parallel and decision: the branches. A decision has two: Order 0 when the condition holds, Order 1 when not."
    Branch: Dict[str, Branch_t] = {}

class Step(SubmodelElementCollection):
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Step/1/0"
    description: str = "One node of the sequence. Kind step: a process of the product. Kind call: the sequence of a part of the bill of material. Kind partial: steps that run in any order their ProcessOrders allow. Kind parallel: branches that all join. Kind conditional: steps that only run when the condition holds. Kind decision: one of two branches, by the condition."
    NodeId: NodeId_t
    Kind: Kind_t
    Name: Union[StepName, Name]
    Order: Order_t
    EstimatedDuration: Optional[EstimatedDuration_t] = None
    ProcessOwner: Optional[ProcessOwner_t] = None
    ProcessReference: Optional[ProcessReference_t] = None
    RequiredCapabilities: Optional[RequiredCapabilities_t] = None
    Joints: Optional[Joints_t] = None
    Outputs: Optional[Outputs_t] = None
    Part: Optional[Part_t] = None
    OccurrenceId: Optional[OccurrenceId_t] = None
    Condition: Optional[Condition_t] = None
    Steps: Optional[Steps_t] = None
    ProcessOrders: Optional[ProcessOrders_t] = None
    Branches: Optional[Branches_t] = None

class Steps(SubmodelElementCollection):
    id_short: AasIdString = "Steps"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0"
    description: str = "The nodes of the sequence."
    Step: Dict[str, Step_t] = {}

class ProductionSequence(Submodel):
    id_short: AasIdString = "ProductionSequence"
    semantic_id: str = "https://smartproductionlab.aau.dk/SubmodelTemplate/ProductionSequence/4/0"
    description: str = "A product's recipe as a partial order (proposed): the steps that make (Assembly) or take apart (Disassembly) the product, each step after the steps it needs, with the joints it makes or breaks. An AAS holds at most one sequence of each archetype. The recipe names no equipment."
    VERSION: ClassVar[str] = "4"
    REVISION: ClassVar[str] = "0"
    ArcheType: ArcheType_t
    Revision: Revision_t
    Name: Name_t
    Subject: Subject_t
    Steps: Steps_t

# alias so field ``RequiredCapability_t`` can name a class of the same id_short
RequiredCapability_t: TypeAlias = RequiredCapability
# alias so field ``JointType_t`` can name a class of the same id_short
JointType_t: TypeAlias = JointType
# alias so field ``JointStandard_t`` can name a class of the same id_short
JointStandard_t: TypeAlias = JointStandard
# alias so field ``Joint_t`` can name a class of the same id_short
Joint_t: TypeAlias = Joint
# alias so field ``JointReference_t`` can name a class of the same id_short
JointReference_t: TypeAlias = JointReference
# alias so field ``OutputId_t`` can name a class of the same id_short
OutputId_t: TypeAlias = OutputId
# alias so field ``DataType_t`` can name a class of the same id_short
DataType_t: TypeAlias = DataType
# alias so field ``Unit_t`` can name a class of the same id_short
Unit_t: TypeAlias = Unit
# alias so field ``Output_t`` can name a class of the same id_short
Output_t: TypeAlias = Output
# alias so field ``Value_t`` can name a class of the same id_short
Value_t: TypeAlias = Value
# alias so field ``OperandType_t`` can name a class of the same id_short
OperandType_t: TypeAlias = OperandType
# alias so field ``StepId_t`` can name a class of the same id_short
StepId_t: TypeAlias = StepId
# alias so field ``ConditionType_t`` can name a class of the same id_short
ConditionType_t: TypeAlias = ConditionType
# alias so field ``EveryNProducts_t`` can name a class of the same id_short
EveryNProducts_t: TypeAlias = EveryNProducts
# alias so field ``CounterScope_t`` can name a class of the same id_short
CounterScope_t: TypeAlias = CounterScope
# alias so field ``Operator_t`` can name a class of the same id_short
Operator_t: TypeAlias = Operator
# alias so field ``Expected_t`` can name a class of the same id_short
Expected_t: TypeAlias = Expected
# alias so field ``Operand_t`` can name a class of the same id_short
Operand_t: TypeAlias = Operand
# alias so field ``Reason_t`` can name a class of the same id_short
Reason_t: TypeAlias = Reason
# alias so field ``ProcessOrder_t`` can name a class of the same id_short
ProcessOrder_t: TypeAlias = ProcessOrder
# alias so field ``BranchId_t`` can name a class of the same id_short
BranchId_t: TypeAlias = BranchId
# alias so field ``Steps_t`` can name a class of the same id_short
Steps_t: TypeAlias = Steps
# alias so field ``Branch_t`` can name a class of the same id_short
Branch_t: TypeAlias = Branch
# alias so field ``NodeId_t`` can name a class of the same id_short
NodeId_t: TypeAlias = NodeId
# alias so field ``Kind_t`` can name a class of the same id_short
Kind_t: TypeAlias = Kind
# alias so field ``Order_t`` can name a class of the same id_short
Order_t: TypeAlias = Order
# alias so field ``EstimatedDuration_t`` can name a class of the same id_short
EstimatedDuration_t: TypeAlias = EstimatedDuration
# alias so field ``ProcessOwner_t`` can name a class of the same id_short
ProcessOwner_t: TypeAlias = ProcessOwner
# alias so field ``ProcessReference_t`` can name a class of the same id_short
ProcessReference_t: TypeAlias = ProcessReference
# alias so field ``RequiredCapabilities_t`` can name a class of the same id_short
RequiredCapabilities_t: TypeAlias = RequiredCapabilities
# alias so field ``Joints_t`` can name a class of the same id_short
Joints_t: TypeAlias = Joints
# alias so field ``Outputs_t`` can name a class of the same id_short
Outputs_t: TypeAlias = Outputs
# alias so field ``Part_t`` can name a class of the same id_short
Part_t: TypeAlias = Part
# alias so field ``OccurrenceId_t`` can name a class of the same id_short
OccurrenceId_t: TypeAlias = OccurrenceId
# alias so field ``Condition_t`` can name a class of the same id_short
Condition_t: TypeAlias = Condition
# alias so field ``ProcessOrders_t`` can name a class of the same id_short
ProcessOrders_t: TypeAlias = ProcessOrders
# alias so field ``Branches_t`` can name a class of the same id_short
Branches_t: TypeAlias = Branches
# alias so field ``Step_t`` can name a class of the same id_short
Step_t: TypeAlias = Step
# alias so field ``ArcheType_t`` can name a class of the same id_short
ArcheType_t: TypeAlias = ArcheType
# alias so field ``Revision_t`` can name a class of the same id_short
Revision_t: TypeAlias = Revision
# alias so field ``Name_t`` can name a class of the same id_short
Name_t: TypeAlias = Name
# alias so field ``Subject_t`` can name a class of the same id_short
Subject_t: TypeAlias = Subject
# ── Resolve forward references (Pydantic circular refs) ──
ArcheType.model_rebuild()
Revision.model_rebuild()
Name.model_rebuild()
Subject.model_rebuild()
NodeId.model_rebuild()
Kind.model_rebuild()
StepName.model_rebuild()
Order.model_rebuild()
EstimatedDuration.model_rebuild()
ProcessOwner.model_rebuild()
ProcessReference.model_rebuild()
RequiredCapability.model_rebuild()
RequiredCapabilities.model_rebuild()
JointType.model_rebuild()
JointStandard.model_rebuild()
Joint.model_rebuild()
JointReference.model_rebuild()
Joints.model_rebuild()
OutputId.model_rebuild()
OutputName.model_rebuild()
DataType.model_rebuild()
Unit.model_rebuild()
Output.model_rebuild()
Outputs.model_rebuild()
Part.model_rebuild()
OccurrenceId.model_rebuild()
ConditionType.model_rebuild()
EveryNProducts.model_rebuild()
CounterScope.model_rebuild()
Operator.model_rebuild()
ConditionUnit.model_rebuild()
ExpectedDataType.model_rebuild()
Value.model_rebuild()
Expected.model_rebuild()
OperandType.model_rebuild()
StepId.model_rebuild()
OperandOutputId.model_rebuild()
Operand.model_rebuild()
Condition.model_rebuild()
Reason.model_rebuild()
ProcessOrder.model_rebuild()
ProcessOrders.model_rebuild()
BranchId.model_rebuild()
BranchName.model_rebuild()
BranchOrder.model_rebuild()
Branch.model_rebuild()
Branches.model_rebuild()
Step.model_rebuild()
Steps.model_rebuild()
ProductionSequence.model_rebuild()
