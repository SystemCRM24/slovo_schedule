from fastapi import APIRouter


router = APIRouter(prefix='/schedule')


@router.post('/create', status_code=200)
async def create(data: int):
        #     const intervals = data.intervals.map(i => `${i.start.getTime()}:${i.end.getTime()}`);
        # const fields = {
        #     ASSIGNED_BY_ID: data.specialist,
        #     [constants.uf.workSchedule.date]: data.date,
        #     [constants.uf.workSchedule.intervals]: intervals
        # }
        # const response = await this._createCrmItem(constants.entityTypeId.workSchedule, fields);
    pass


@router.get('/get', status_code=200)
async def get():
    # return await this._getCrmItem(constants.entityTypeId.workSchedule, id);
    pass


@router.put('/put', status_code=200)
async def put():
        #     const intervals = data.intervals.map(i => `${i.start.getTime()}:${i.end.getTime()}`);
        # const fields = {
        #     ASSIGNED_BY_ID: data.specialist,
        #     [constants.uf.workSchedule.date]: data.date,
        #     [constants.uf.workSchedule.intervals]: intervals
        # }
        # const response = await this._updateCrmItem(constants.entityTypeId.workSchedule, id, fields);
        # return response.item;
    pass


@router.delete('/delete', status_code=200)
async def delete():
    # return await this._deleteCrmItem(constants.entityTypeId.workSchedule, id);
    pass
