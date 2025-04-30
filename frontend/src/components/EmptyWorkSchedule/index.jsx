import React, {useState} from 'react';
import {Button} from "react-bootstrap";
import AddWorkScheduleModal from "../../AddWorkScheduleModal/index.jsx";

const EmptyWorkSchedule = () => {
    const [showModal, setShowModal] = useState(false);
    return (
        <>
            <div className={'d-flex flex-column align-items-center justify-content-center gap-2'}>
                <div className={'text-center text-secondary'} style={{fontSize: "1.5rem"}}>График работы не задан</div>
                <Button variant={'outline-success'} onClick={() => !showModal && setShowModal(true)}>Задать график работы</Button>
            </div>
            <AddWorkScheduleModal show={showModal} setShow={setShowModal} />
        </>
    );
};

export default React.memo(EmptyWorkSchedule);