import React, {useMemo, useState} from 'react';
import './WorkingInterval.css';
import {getIntervalTimeString} from "../../utils/dates.js";
import EditWorkScheduleModal from "../EditWorkScheduleModal/index.jsx";
import EditAppointmentModal from '../EditAppointmentModal/index.jsx';
import {useChildrenContext} from "../../contexts/Children/provider.jsx";


const WorkingInterval = ({id, startDt, endDt, percentOfWorkingDay, status, patientId, patientType}) => {
    const [showModal, setShowModal] = useState(false);
    const patients = useChildrenContext();
    const patientName = useMemo(() => {
        return patients?.[patientId]
    }, [patientId, patients]);
    return (
        <div
            style={{height: `${percentOfWorkingDay}%`, fontSize: percentOfWorkingDay < 3 ? "8pt" : "small"}}
            className={`interval status-${status} d-flex flex-column align-items-center justify-content-center`}
            onClick={() => {
                !showModal && setShowModal(true)
            }}
        >
            {patientId && <div className={'fw-bold'}>{patientName} {patientType}</div>}
            <div>
                {getIntervalTimeString(startDt, endDt)}
            </div>
            {status === "free" &&
                <EditWorkScheduleModal show={showModal} setShow={setShowModal} startDt={startDt} endDt={endDt}/>
            }
            {(status === "booked" || status === 'confirmed') &&
                <EditAppointmentModal id={id} show={showModal} setShow={setShowModal} startDt={startDt} endDt={endDt}
                                      patientId={patientId} patientType={patientType} status={status}/>
            }

        </div>
    );
};

export default React.memo(WorkingInterval);