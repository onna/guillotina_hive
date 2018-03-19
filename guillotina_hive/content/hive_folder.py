from guillotina import configure
from guillotina.constraintypes import FTIConstrainAllowedTypes
from guillotina.interfaces import IConstrainTypes
from guillotina_hive.interfaces import IHiveFolder


@configure.adapter(for_=IHiveFolder, provides=IConstrainTypes)
class HiveAllowedTypes(FTIConstrainAllowedTypes):

    def get_allowed_types(self) -> list:
        return ['DistTask', 'Task']
