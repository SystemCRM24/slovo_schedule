import React, {useMemo, useState} from 'react';
import './WorkingInterval.css';
import {getIntervalTimeString} from "../../utils/dates.js";
import EditWorkScheduleModal from "../EditWorkScheduleModal/index.jsx";
import EditAppointmentModal from '../EditAppointmentModal/index.jsx';
import {useChildrenContext} from "../../contexts/Children/provider.jsx";
import EditNAIntervalModal from "../EditNAIntervalModal/index.jsx";


const WorkingInterval = ({id, startDt, endDt, percentOfWorkingDay, status, patientId, patientType}) => {
    const [showModal, setShowModal] = useState(false);
    const patients = useChildrenContext();
    const patientName = useMemo(() => {
        const patientName = patients?.[patientId];
        if ( patientName ) {
            const splitName = patientName.split(' ');
            if ( splitName.length > 2 ) {
                return splitName.splice(0, 2).join(' ');
            }
        }
        return patientName;
    }, [patientId, patients]);

    return (
        <div
            className={`interval status-${status}`}
            style={{height: '2.5rem'}}
            onClick={() => { !showModal && setShowModal(true) }}
        >
            <div 
                style={{
                    display: 'flex', 
                    flexDirection: 'column',
                    paddingRight: '0.5rem',
                    paddingLeft: '0.5rem'
                }}
            >
                <div>{getIntervalTimeString(startDt, endDt)}</div>
                {patientId && 
                    <div 
                        className={'fw-bold'}
                        style={{marginLeft: 'auto'}}
                    >
                        {patientName} {patientType}
                    </div>
                }
            </div> 
            {status === "na" &&
                <EditNAIntervalModal show={showModal} setShow={setShowModal} startDt={startDt} endDt={endDt}/>
            }
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