from classes_out import ListenHistoryOut, TracksOut, UsersOut
from fastapi import FastAPI, Query, Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import RedirectResponse
from fastapi_pagination import Page, add_pagination, paginate, Params
from generate_fake_data import FakeDataGenerator

# N'est plus disponible dans la version actuelle de fastapi-pagination

# Page = Page.with_custom_options(
#     size=Query(100, ge=1, le=100),
# )
 

class CustomParams(Params):
    @classmethod
    def from_query(
        cls,
        page: int = Query(1, ge=1),
        size: int = Query(100, ge=1, le=100),
    ):
        return cls(page=page, size=size)

app = FastAPI(
    title="MooVitamix",
    description="A music recommendation system.",
    version="1.1",
    docs_url=None,
)


@app.get("/")
async def docs_redirect():
    return RedirectResponse(url="/docs")


@app.get("/docs", include_in_schema=False)
async def overridden_swagger():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="MooVitamix",
        swagger_favicon_url="https://moov.ai/wp-content/uploads/2019/07/cropped-favicon-1-32x32.png",
    )


data_range_observations = 1000
generator = FakeDataGenerator(data_range_observations)
tracks, users, listen_history = generator.generate_fake_data()


@app.get("/tracks", tags=["HTTP methods"])
async def get_tracks(params: CustomParams = Depends()) -> Page[TracksOut]:
    return paginate(tracks, params)


@app.get("/users", tags=["HTTP methods"])
async def get_users(params: CustomParams = Depends()) -> Page[UsersOut]:
    return paginate(users, params)


@app.get("/listen_history", tags=["HTTP methods"])
async def get_listen_history(params: CustomParams = Depends()) -> Page[ListenHistoryOut]:
    return paginate(listen_history, params)


add_pagination(app)
