import './App.css'
import DateRangePicker from "./components/ui/DateRangePicker/index.jsx";
import {useState} from "react";
import {Container} from "react-bootstrap";
import Schedule from "./components/Schedule/index.jsx";

function App() {
    const [dates, setDates] = useState({fromDate: undefined, toDate: undefined})
    const onDatesChange = e => {
        const dateType = e.target.name;
        setDates({...dates, [dateType]: e.target.valueAsDate,});
        console.log(dates);
    }
    return (
        <Container fluid>
            <DateRangePicker onChange={onDatesChange} dates={dates}/>
            <Schedule {...dates} />
        </Container>
    )
}

export default App
