import React, { useMemo, useState, useContext } from 'react';
import './WorkingInterval.css';
import { getIntervalTimeString, getWorkingIntervalsFromSchedules } from "../../utils/dates.js";
import EditWorkScheduleModal from "../EditWorkScheduleModal/index.jsx";
import EditAppointmentModal from '../EditAppointmentModal/index.jsx';
import { useChildrenContext } from "../../contexts/Children/provider.jsx";
import EditNAIntervalModal from "../EditNAIntervalModal/index.jsx";
import useSchedules from '../../hooks/useSchedules.js';
import EditClientInfoModal from '../EditClientInfoModal/index.jsx';
import { useSpecialistContext } from "../../contexts/Specialist/provider.jsx";
import { AppContext } from '../../contexts/App/context.js';


const WorkingInterval = ({ id, startDt, endDt, percentOfWorkingDay, status, patientId, patientType, patientCode }) => {
    const [showModal, setShowModal] = useState(false);
    const [showModalEdit, setShowModalEdit] = useState(false);
    const { schedule, workSchedule } = useSchedules();
    const specialistId = useSpecialistContext();

    const oldpatientId = useMemo(
        () => {
            for (const item of schedule) {
                if (item.id === id) {
                    return item.old_patient;
                }
            }
            return 0;
        },
        [id, schedule, patientId]
    );

    const intervalStatus = useMemo(
        () => {
            if ( status === 'free' ) {
                return status;
            }
            if ( id && schedule.length > 0 ) {
                for ( const item of schedule ) {
                    if ( item.id !== id ) {
                        continue;
                    }
                    let status = item.status === 'Единичное' ? 'single' : 'multiple';
                    const isSpecialistChanged = item.old_specialist != specialistId;
                    const isPatientChanged = item.old_patient != item.patient.id;
                    const itemStart = item.start.getTime();
                    const isStartChanged = item.old_start.getTime() !== itemStart;
                    const itemEnd = item.end.getTime();
                    const isEndChanged = item.old_end.getTime() !== itemEnd;
                    const isCodeChanged = item.old_code != item.patient.type;
                    const isStatusChanged = item.status != item.old_status;
                    if (isSpecialistChanged || isPatientChanged || isStartChanged || isEndChanged || isCodeChanged || isStatusChanged) {
                        status = 'replace';
                    }
                    let isOffSchedule = true;
                    for ( const interval of workSchedule.intervals ) {
                        if ( interval.start.getTime() <= itemStart && interval.end.getTime() >= itemEnd ) {
                            isOffSchedule = false;
                        }
                    }
                    if ( isOffSchedule ) {
                        status = 'skip';
                    }
                    return status;
                }
            }
            return 'na';
        },
        [schedule, id, status, specialistId, workSchedule]
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

    const {increaseModalCount} = useContext(AppContext);

    const onIntervalClick = () => {
        if ( !showModal && !showModalEdit ) {
            increaseModalCount();
            setShowModal(true);
        }
    }

    return (
        <div
            className={`interval status-${intervalStatus}`}
            style={{ height: '2.5rem' }}
            onClick={onIntervalClick}
        >
            <div
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    paddingRight: '0.5rem',
                    paddingLeft: '0.5rem'
                }}
            >
                <div style={patientName ? { marginRight: 'auto' } : { margin: 'auto' }}>
                    {getIntervalTimeString(startDt, endDt)}
                </div>
                {patientId &&
                    <div className={'fw-bold'} style={{ marginLeft: 'auto' }}>
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
            {(intervalStatus === "single" || intervalStatus === 'multiple' || intervalStatus === 'skip' || intervalStatus === 'replace') &&
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
                    <EditClientInfoModal show={showModalEdit} setShow={setShowModalEdit} id={id} />
                </>

            }
        </div>
    );
};

export default WorkingInterval;