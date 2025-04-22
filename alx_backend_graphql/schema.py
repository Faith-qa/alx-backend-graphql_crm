import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

class Query(CRMQuery, graphene.ObjectType):
    # This class inherits all queries from CRMQuery
    hello = graphene.String(default_value="Hello, GraphQL!")

class Mutation(CRMMutation, graphene.ObjectType):
    # This class inherits all mutations from CRMMutation
    pass

schema = graphene.Schema(query=Query, mutation=Mutation) 