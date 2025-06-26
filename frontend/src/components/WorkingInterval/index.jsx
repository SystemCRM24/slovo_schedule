import React, { useMemo, useState } from 'react';
import './WorkingInterval.css';
import { getIntervalTimeString } from "../../utils/dates.js";
import EditWorkScheduleModal from "../EditWorkScheduleModal/index.jsx";
import EditAppointmentModal from '../EditAppointmentModal/index.jsx';
import { useChildrenContext } from "../../contexts/Children/provider.jsx";
import EditNAIntervalModal from "../EditNAIntervalModal/index.jsx";
import useSchedules from '../../hooks/useSchedules.js';
import EditClientInfoModal from '../EditClientInfoModal/index.jsx';

const WorkingInterval = ({ id, startDt, endDt, percentOfWorkingDay, status, patientId, patientType }) => {
    const [showModal, setShowModal] = useState(false);
    const [showModalEdit, setShowModalEdit] = useState(false);
    const { schedule } = useSchedules();

    const oldpatientId = useMemo(
        () => schedule[0]?.old_patient || 0,
        [schedule, patientId]
    );
    const intervalStatus = useMemo(
        () => {
            if (status) {
                return status;
            }
            if (schedule.length > 0) {
                const oldPatient = schedule[0].old_patient;
                if (oldpatientId && oldpatientId !== patientId) {
                    return 'replace';
                }
                return 'booked';
            }
            return 'na';
        },
        [schedule, status, patientId]
    );

    const patients = useChildrenContext();
    const patientName = useMemo(() => {
        const patientName = patients?.[patientId];
        if (patientName) {
            const splitName = patientName.split(' ');
            if (splitName.length > 2) {
                return splitName.splice(0, 2).join(' ');
            }
        }
        return patientName;
    }, [patientId, patients]);

    return (
        <div
            className={`interval status-${intervalStatus}`}
            style={{ height: '2.5rem' }}
            onClick={() => { (!showModal && !showModalEdit) && setShowModal(true) }}
        >
            <div
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    paddingRight: '0.5rem',
                    paddingLeft: '0.5rem'
                }}
            >
                <div style={patientName ? { marginRight: 'auto' } : { margin: 'auto' }}>{getIntervalTimeString(startDt, endDt)}</div>
                {patientId &&
                    <div
                        className={'fw-bold'}
                        style={{ marginLeft: 'auto' }}
                    >
                        {patientName} {patientType}
                    </div>
                }
            </div>
            {intervalStatus === "na" &&
                <EditNAIntervalModal show={showModal} setShow={setShowModal} startDt={startDt} endDt={endDt} />
            }
            {intervalStatus === "free" &&
                <EditWorkScheduleModal show={showModal} setShow={setShowModal} startDt={startDt} endDt={endDt} />
            }
            {(intervalStatus === "booked" || intervalStatus === 'skip' || intervalStatus === 'replace') &&
                <>
                    <EditAppointmentModal
                        id={id}
                        show={showModal}
                        setShow={setShowModal}
                        startDt={startDt}
                        endDt={endDt}
                        patientId={patientId}
                        patientType={patientType}
                        status={intervalStatus}
                        oldpatientId={oldpatientId}
                        showModalEdit={showModalEdit}
                        setShowModalEdit={setShowModalEdit}
                    />
                    <EditClientInfoModal show={showModalEdit} setShow={setShowModalEdit} id={id}/>
                </>

            }
        </div>
    );
};

export default WorkingInterval;