import React, {useContext, useState} from 'react';
import {Button} from "react-bootstrap";
import AddWorkScheduleModal from "../AddWorkScheduleModal/index.jsx";
import { AppContext } from '../../contexts/App/context.js';



const EmptyWorkSchedule = () => {
    const [showModal, setShowModal] = useState(false);

    const {increaseModalCount} = useContext(AppContext);

    const onCLick = () => {
        if ( !showModal ) {
            increaseModalCount();
            setShowModal(true);
        }
    };


    return (
        <>
            <div className={'d-flex flex-column align-items-center justify-content-center gap-2'}>
                <div className={'text-center text-secondary'} >График не задан</div>
                <Button variant={'outline-success'} onClick={onCLick}>Задать график</Button>
            </div>
            <AddWorkScheduleModal show={showModal} setShow={setShowModal} />
        </>
    );
};

export default EmptyWorkSchedule;