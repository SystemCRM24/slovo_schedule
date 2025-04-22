import React from 'react';
import {Form} from "react-bootstrap";
import {getISODate} from "../../../utils/dates.js";

const DateRangePicker = ({dates, onChange}) => {
    return (
        <div>
            <div>
                <label htmlFor="fromDate">От:</label>
                <Form.Control type="date" name="fromDate" id="fromDate" onChange={onChange}/>
            </div>
            <div>
                <label htmlFor="toDate">До:</label>
                <Form.Control type="date" name="toDate" id="toDate" onChange={onChange} min={getISODate(dates.fromDate)}/>
            </div>
        </div>
    );
};

export default DateRangePicker;