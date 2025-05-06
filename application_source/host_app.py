from fastapi import FastAPI

from controller.host_controller import HostController

app = FastAPI(debug=True)
controller = HostController()
app.include_router(controller.router)