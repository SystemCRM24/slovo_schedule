import React from 'react';
import {Form} from "react-bootstrap";
import {getISODate} from "../../../utils/dates.js";

const DateRangePicker = ({dates, onChange}) => {
    return (
        <div className={'d-flex flex-column gap-3'}>
            <div>
                <label htmlFor="fromDate" className={'mb-1'}>От:</label>
                <Form.Control type="date" name="fromDate" id="fromDate" onChange={onChange}/>
            </div>
            <div>
                <label htmlFor="toDate" className={'mb-1'}>До:</label>
                <Form.Control
                    type="date"
                    name="toDate"
                    id="toDate"
                    onChange={onChange}
                    min={getISODate(dates.fromDate)}
                    disabled={!dates.fromDate}
                />
            </div>
        </div>
    );
};

export default DateRangePicker;