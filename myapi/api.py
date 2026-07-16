from ninja_extra import NinjaExtraAPI

from .search_controller import SearchController
from .ssg_controller import SSGController
from .company_controller import CompanyController
from .hubs_controller import HubsController
from .forms_controller import FormsController

api_v1 = NinjaExtraAPI(version="1.0.0", title="Pexus API", description="Production APIs for MVP")

api_v1.register_controllers(
    SearchController,
    SSGController,
    CompanyController,
    HubsController,
    FormsController
)