import React, {useState, useMemo, useEffect, useCallback, useContext} from 'react';
import {Button, Form} from "react-bootstrap";
import { DateTime } from 'luxon';
import { AppContext } from '../../../contexts/App/context';

import './DateRangePicker.css'

const DateRangePicker = () => {
    const { setDates } = useContext(AppContext);

    const [startOfWeek, endOfWeek] = useMemo(
        () => {
            // const now = DateTime.utc();
            // const startOfWeek = now.startOf('week');
            // const endOfWeek = now.endOf('week').minus({'hours': 3});
            const startOfWeek = DateTime.fromObject({ year: 2025, month: 5, day: 5 }, { zone: 'utc' }).startOf('day');
            const endOfWeek = DateTime.fromObject({ year: 2025, month: 5, day: 7 }, { zone: 'utc' }).endOf('day').minus({'hours': 3});
            return [startOfWeek.toUTC().toJSDate(), endOfWeek.toUTC().toJSDate()];
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
        console.log(start, end);
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