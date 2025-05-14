from fastapi import APIRouter


router = APIRouter(prefix='/appointment')


@router.post('/create', status_code=200)
async def create(data: int):
        #     const fields = {
        #     ASSIGNED_BY_ID: data.specialist,
        #     [constants.uf.appointment.patient]: data.patient,
        #     [constants.uf.appointment.start]: data.start,
        #     [constants.uf.appointment.end]: data.end,
        #     [constants.uf.appointment.status]: constants.listFieldValues.appointment.idByStatus[data.status],
        #     [constants.uf.appointment.code]: constants.listFieldValues.appointment.idByCode[data.code]
        # };
        # const response = await this._createCrmItem(constants.entityTypeId.appointment, fields);
    pass


@router.get('/get', status_code=200)
async def get():

    pass


@router.put('/put', status_code=200)
async def put():
        #     const fields = {
        #     ASSIGNED_BY_ID: data.specialist,
        #     [constants.uf.appointment.patient]: data.patient,
        #     [constants.uf.appointment.start]: data.start,
        #     [constants.uf.appointment.end]: data.end,
        #     [constants.uf.appointment.status]: constants.listFieldValues.appointment.idByStatus[data.status],
        #     [constants.uf.appointment.code]: constants.listFieldValues.appointment.idByCode[data.code]
        # };
        # const response = await this._updateCrmItem(constants.entityTypeId.appointment, id, fields);
    pass


@router.delete('/delete', status_code=200)
async def delete():
    # return await this._deleteCrmItem(constants.entityTypeId.appointment, id);
    pass
