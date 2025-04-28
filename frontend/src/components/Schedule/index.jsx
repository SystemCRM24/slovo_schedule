import React, {Suspense, useEffect, useState, useMemo} from 'react';
import {Spinner, Table} from "react-bootstrap";

import DaySchedule from '../DaySchedule';
import apiClient from "../../api/";
import {useScheduleContext} from "../../contexts/Schedule/provider.jsx";
import {useWorkScheduleContext} from "../../contexts/WorkSchedule/provider.jsx";


const Schedule = ({fromDate, toDate}) => {
    const [specialists, setSpecialists] = useState([]);
    const [schedule, setSchedule] = useScheduleContext();
    const [workSchedule, setWorkSchedule] = useWorkScheduleContext();

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
            for (const [name, attr] of Object.entries(specialists)) {
                const codes = attr.departments.join(', ');
                headers.push((
                    <th
                        scope="col"
                        style={{width: 400, whiteSpace: 'pre-wrap'}}
                        key={name}
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
            let currentDate = new Date(fromDate);
            const style = {height: '800px'};
            while (currentDate <= toDate) {
                const row = [];
                const dayOfWeek = currentDate.toLocaleString('ru-RU', {weekday: 'long'});
                const date = currentDate.toLocaleDateString();
                row.push((
                    <th scope={'row'} key={date}>{dayOfWeek}<br/>{date}</th>
                ));
                for (const specialist of Object.keys(specialists)) {
                    const cell = (
                        <DaySchedule key={`${specialist}_${date}`} specialist={specialist}
                                     date={new Date(currentDate)}/>);
                    row.push(cell)
                }
                rows.push((<tr style={style} key={`row_${date}`}>{row}</tr>))
                currentDate.setDate(currentDate.getDate() + 1);
            }
            return rows;
        },
        [fromDate, toDate, specialists]
    );
    return (fromDate && toDate) && (
        <Suspense fallback={<Spinner animation={"grow"}/>}>
            <ul
                style={{
                    listStyle: 'none', height: 30, display: "flex",
                    justifyContent: "space-around", marginTop: '.75rem'
                }}
            >
                {Object.entries({'free': 'Свободно', 'booked': "Забронировано", 'confirmed': "Подтверждено"}).map(
                    ([status, label]) => {
                        return (
                            <li className={`me-2 d-flex align-items-center justify-content-between`}
                                style={{float: "left"}}>
                                <span className={`status-${status}`}
                                      style={{width: 12, height: 12, float: "left", marginRight: ".5rem"}}
                                ></span>
                                {label}
                            </li>
                        )
                    }
                )}
            </ul>
            <Table bordered responsive className={'mt-3'} style={{minWidth: `250%`}}>
                <thead>
                <tr>
                    <th scope="col" style={{width: 200}}/>
                    {headers}
                </tr>
                </thead>
                <tbody>
                {rows}
                </tbody>
            </Table>
        </Suspense>
    );
};

export default React.memo(Schedule);