import React, {useState} from 'react';
import './WorkingInterval.css';
import {getIntervalTimeString} from "../utils/dates.js";
import CustomModal from "../components/ui/Modal/index.jsx";

const WorkingInterval = ({startDt, endDt, percentOfWorkingDay, status, patientName, patientType}) => {
    const [showModal, setShowModal] = useState(false);
    return (
        <div
            style={{height: `${percentOfWorkingDay}%`}}
            className={`interval status-${status} d-flex flex-column align-items-center justify-content-center`}
            onClick={() => {
                !showModal && setShowModal(true)
            }}
        >
            {patientName && <div className={'fw-bold'}>{patientName} {patientType}</div>}
            <div>
                {getIntervalTimeString(startDt, endDt)}
            </div>
            <CustomModal
                show={showModal}
                handleClose={() => {
                    setShowModal(false)
                }}
                title={'Test'}
            >
                Test
            </CustomModal>
        </div>
    );
};

export default React.memo(WorkingInterval);