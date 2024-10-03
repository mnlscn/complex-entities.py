from pydantic import BaseModel, Field
from typing import List
from graphviz import Digraph


class Property(BaseModel):
    key: str
    value: str
    resolved_absolute_value: str


class Entity(BaseModel):
    id: int = Field(
        ...,
        description="Unique identifier for the entity, used for deduplication, design a scheme allows multiple entities",
    )
    subquote_string: List[str] = Field(
        ...,
        description="Correctly resolved value of the entity, if the entity is a reference to another entity, this should be the id of the referenced entity, include a few more words before and after the value to allow for some context to be used in the resolution",
    )
    entity_title: str
    properties: List[Property] = Field(
        ..., description="List of properties of the entity"
    )
    dependencies: List[int] = Field(
        ...,
        description="List of entity ids that this entity depends  or relies on to resolve it",
    )


class DocumentExtraction(BaseModel):
    entities: List[Entity] = Field(
        ...,
        description="Body of the answer, each fact should be a separate object with a body and a list of sources",
    )


import instructor
from openai import OpenAI

# Apply the patch to the OpenAI client
# enables response_model keyword
client = instructor.from_openai(OpenAI())


def ask_ai(content) -> DocumentExtraction:
    return client.chat.completions.create(
        model="gpt-4o",
        response_model=DocumentExtraction,
        messages=[
            {
                "role": "system",
                "content": "Extract and resolve a list of entities from the following document:",
            },
            {
                "role": "user",
                "content": content,
            },
        ],
    )  # type: ignore


def generate_html_label(entity: Entity) -> str:
    rows = [
        f"<tr><td>{prop.key}</td><td>{prop.resolved_absolute_value}</td></tr>"
        for prop in entity.properties
    ]
    table_rows = "".join(rows)
    return f"<<table border='0' cellborder='1' cellspacing='0'><tr><td colspan='2'><b>{entity.entity_title}</b></td></tr>{table_rows}</table>>"


def generate_graph(data: DocumentExtraction):
    dot = Digraph(comment="Entity Graph", node_attr={"shape": "plaintext"})

    for entity in data.entities:
        label = generate_html_label(entity)
        dot.node(str(entity.id), label)

    for entity in data.entities:
        for dep_id in entity.dependencies:
            dot.edge(str(entity.id), str(dep_id))

    dot.render("entity.gv", view=True)


content = """
Sample Legal Contract
Agreement Contract

This Agreement is made and entered into on 2020-01-01 by and between Company A ("the Client") and Company B ("the Service Provider").

Article 1: Scope of Work

The Service Provider will deliver the software product to the Client 30 days after the agreement date.

Article 2: Payment Terms

The total payment for the service is $50,000.
An initial payment of $10,000 will be made within 7 days of the the signed date.
The final payment will be due 45 days after [SignDate].

Article 3: Confidentiality

The parties agree not to disclose any confidential information received from the other party for 3 months after the final payment date.

Article 4: Termination

The contract can be terminated with a 30-day notice, unless there are outstanding obligations that must be fulfilled after the [DeliveryDate].
"""  # Your legal contract here
model = ask_ai(content)
generate_graph(model)

