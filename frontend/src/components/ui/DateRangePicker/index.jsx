import React, {useMemo} from 'react';
import {Form} from "react-bootstrap";
import {getISODate} from "../../../utils/dates.js";

const DateRangePicker = ({dates, onChange}) => {
    const [start, end] = useMemo(
        () => {
            const now = new Date();
            const dayOfWeek = now.getDay();

            const startOfWeek = new Date(now);
            startOfWeek.setDate(now.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));
            startOfWeek.setHours(0, 0, 0, 0);

            const endOfWeek = new Date(startOfWeek);
            endOfWeek.setDate(startOfWeek.getDate() + 6);
            endOfWeek.setHours(23, 59, 59, 999);

            return [startOfWeek, endOfWeek].map(d => d.toISOString().split('T')[0]);
        },
        []
    );

    return (
        <div className={'d-flex flex-column gap-3'}>
            <div>
                <label htmlFor="fromDate" className={'mb-1'}>От:</label>
                <Form.Control 
                    type="date" 
                    name="fromDate" 
                    id="fromDate"
                    onChange={onChange}
                    value={start}
                />
            </div>
            <div>
                <label htmlFor="toDate" className={'mb-1'}>До:</label>
                <Form.Control
                    type="date"
                    name="toDate"
                    id="toDate"
                    onChange={onChange}
                    value={end}
                    min={getISODate(dates.fromDate)}
                    disabled={!dates.fromDate}
                />
            </div>
        </div>
    );
};

export default DateRangePicker;