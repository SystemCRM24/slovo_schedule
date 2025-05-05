import React, {useMemo, useState} from 'react';
import './WorkingInterval.css';
import {getIntervalTimeString} from "../../utils/dates.js";
import EditWorkScheduleModal from "../EditWorkScheduleModal/index.jsx";
import EditAppointmentModal from '../EditAppointmentModal/index.jsx';


const WorkingInterval = ({startDt, endDt, percentOfWorkingDay, status, patientName, patientType}) => {
    const [showModal, setShowModal] = useState(false);

    return (
        <div
            style={{height: `${percentOfWorkingDay}%`, fontSize: percentOfWorkingDay < 3 ? "8pt" : "small"}}
            className={`interval status-${status} d-flex flex-column align-items-center justify-content-center`}
            onClick={() => {
                !showModal && setShowModal(true)
            }}
        >
            {patientName && <div className={'fw-bold'}>{patientName} {patientType}</div>}
            <div>
                {getIntervalTimeString(startDt, endDt)}
            </div>
            {status === "free" &&
                <EditWorkScheduleModal show={showModal} setShow={setShowModal} startDt={startDt} endDt={endDt}/>
            }
            {(status === "booked" || status === 'confirmed') &&
                <EditAppointmentModal show={showModal} setShow={setShowModal} startDt={startDt} endDt={endDt}
                                      patientName={patientName} patientType={patientType} status={status}/>
            }

        </div>
    );
};

export default React.memo(WorkingInterval);