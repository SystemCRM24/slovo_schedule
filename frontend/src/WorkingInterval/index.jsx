import React from 'react';
import './WorkingInterval.css';
import {getIntervalTimeString} from "../utils/dates.js";
const WorkingInterval = ({startDt, endDt, percentOfWorkingDay, status, patientName, patientType}) => {
    console.log(startDt, endDt);
    return (
        <div
            style={{height: `${percentOfWorkingDay}%`}}
            className={`interval status-${status} d-flex flex-column align-items-center justify-content-center`}>
            {patientName && <div className={'fw-bold'}>{patientName} {patientType}</div>}
            <div>
                {getIntervalTimeString(startDt, endDt)}
            </div>
        </div>
    );
};

export default React.memo(WorkingInterval);