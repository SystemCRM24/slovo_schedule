import React from 'react';
import {Button} from "react-bootstrap";

const EmptyWorkSchedule = () => {
    return (
        <div className={'d-flex flex-column align-items-center justify-content-center gap-2'}>
            <div className={'text-center text-secondary'} style={{fontSize: "1.5rem"}}>График работы не задан</div>
            <Button variant={'outline-success'}>Задать график работы</Button>
        </div>
    );
};

export default React.memo(EmptyWorkSchedule);