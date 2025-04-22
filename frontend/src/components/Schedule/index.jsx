import React, {Suspense, useEffect, useState, useMemo} from 'react';
import {Spinner, Table} from "react-bootstrap";

import DaySchedule from '../DaySchedule';
import apiClient from "../../api/";


const Schedule = ({fromDate, toDate}) => {
    const [specialists, setSpecialists] = useState([]);
    const [schedule, setSchedule] = useState({});
    const [workSchedule, setWorkSchedule] = useState({});

    useEffect(() => {
        (async () => {
            setSpecialists(await apiClient.getSpecialists());
        })();
    }, []);

    useEffect(() => {
        (async () => {
            if (fromDate && toDate) {
                const [scheduleData, workScheduleData] = await Promise.all([
                    apiClient.getSchedule(fromDate, toDate),
                    apiClient.getWorkSchedule(fromDate, toDate)
                ]);
                setSchedule(scheduleData);
                setWorkSchedule(workScheduleData);
            }
        })();
    }, [fromDate, toDate]);

    const headers = useMemo(
        () => {
            const headers = [];
            for ( const [name, attr] of Object.entries(specialists) ) {
                const codes = attr.departments.join(', ');
                headers.push((
                    <th 
                        scope="col" 
                        style={{width: 400, whiteSpace: 'pre-wrap'}}
                    >
                        {name + '\n' + codes}
                    </th>
                ));
            }
            return headers;
        },
        [specialists]
    );

    const rows = useMemo(
        () => {
            const rows = [];
            let start = new Date(fromDate);
            const style = {height: '200px'};
            while ( start <= toDate ) {
                const row = [];
                const dayOfWeek = start.toLocaleString('ru-RU', {weekday: 'long'});
                const date = start.toLocaleDateString();
                row.push((
                    <td>{dayOfWeek}<br/>{date}</td>
                ));
                for ( const specialist of Object.keys(specialists) ) {
                    const scheduleOfDay = schedule[specialist]?.[start];
                    const workScheduleOfDay = workSchedule[specialist]?.[start];
                    const cell = (<DaySchedule schedule={scheduleOfDay} workSchedule={workScheduleOfDay}></DaySchedule>);
                    row.push(cell)
                }
                rows.push((<tr style={style}>{row}</tr>))
                start.setDate(start.getDate() + 1);
            }
            return rows;
        },
        [fromDate, toDate, specialists, schedule, workSchedule]
    );

    return Object.keys(schedule).length ? (
        <Suspense fallback={<Spinner animation={"grow"} />}>
            <Table bordered responsive className={'mt-3'} style={{minWidth: "200%"}}>
                <thead>
                    <tr>
                        <th scope="col" style={{width: 200}} />
                        {headers}
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </Table>
        </Suspense>
    ) : <></>;
};

export default React.memo(Schedule);