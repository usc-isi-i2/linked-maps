class Node:
    def __init__(self, metadata, gid):
        self.metadata = metadata
        self.gid = gid


    def intersect(self, other_node):
        pass

    def union(self, other_node):
        pass


    def minus(self, other_node):
        pass

    @classmethod
    def from_shapefile(cls, path, metadata):
        # TODO
        gid = 0
        node = cls(metadata, gid)
        return node



class Metadata:
    def __init__(self, conn, db_name, table_name):
        self.conn = conn
        self.db_name = db_name
        self.table_name = table_name