import React, {useState, useMemo, useEffect, useCallback} from 'react';
import {Button, Form} from "react-bootstrap";

import './DateRangePicker.css'

const DateRangePicker = ({setDates}) => {

    const [startOfWeek, endOfWeek] = useMemo(
        () => {
            const now = new Date();
            const dayOfWeek = now.getDay();
            now.getMo
            const startOfWeek = new Date(now);
            startOfWeek.setDate(now.getDate() - (dayOfWeek === 0 ? 6 : (dayOfWeek - 1)));
            startOfWeek.setHours(0, 0, 0, 0);

            const endOfWeek = new Date(startOfWeek);
            endOfWeek.setDate(startOfWeek.getDate() + 6);
            endOfWeek.setHours(23, 59, 59, 999);

            return [startOfWeek, endOfWeek];
        },
        []
    );

    const getLocalISODate = useCallback(
        date => {
            if ( date ) {
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                return `${year}-${month}-${day}`;
            }
        }
    )

    const [start, setStart] = useState(startOfWeek);
    const startISO = useMemo(() => getLocalISODate(start), [start]);

    const [end, setEnd] = useState(endOfWeek);
    const endISO = useMemo(() => getLocalISODate(end), [end])

    useEffect(
        () => {
            if ( start && end ) {
                if ( start >= end ) {
                    setEnd(start);
                }
            }
        },
        [start, end, setEnd]
    );

    const onSubmit = (e) => {
        e.preventDefault();
        setDates({fromDate: start, toDate: end});
    }

    return (
        <Form onSubmit={onSubmit}>
            <div id='DateRangePicker'>
                <div>
                    <label htmlFor="fromDate" className={'mb-1'}>От:</label>
                    <Form.Control
                        type='date'
                        name='fromDate'
                        id='fromDate'
                        required
                        value={startISO}
                        onChange={e => setStart(e.target.valueAsDate)}
                    />
                    </div>
                <div>
                    <label htmlFor="toDate" className={'mb-1'}>До:</label>
                    <Form.Control
                        type='date'
                        name='fromDate'
                        id='fromDate'
                        required
                        value={endISO}
                        onChange={e => setEnd(e.target.valueAsDate)}
                    />
                </div>
                <Button variant='success' type='submit'>Принять</Button>
            </div>

        </Form>
    );
};

export default DateRangePicker;