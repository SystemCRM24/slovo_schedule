import React, {Suspense, useEffect, useState} from 'react';
import {Table} from "react-bootstrap";
import apiClient from "../../api/";

const Schedule = ({fromDate, toDate}) => {
    const [specialists, setSpecialists] = useState([]);
    const [schedule, setSchedule] = useState({});
    useEffect(() => {
        (async () => {
            setSpecialists(await apiClient.getSpecialists());
        })();
    }, []);

    useEffect(() => {
        (async () => {
            console.log('effect call');
            setSchedule(await apiClient.getSchedule(fromDate, toDate));
        })();
    }, [fromDate, toDate]);
    return (
        <Suspense fallback={<div>Loading</div>}>
            {(fromDate && toDate) ? JSON.stringify(schedule) : "Заполните даты для отображения расписания"}
            <Table bordered responsive>
            </Table>
        </Suspense>
    );
};

export default React.memo(Schedule);