import React from "react";
import {Button, Modal} from "react-bootstrap";

export default function CustomModal({
    show,
    handleClose, 
    handlePrimaryBtnClick, 
    primaryBtnText,
    primaryBtnDisabled = true,
    title,
    size = 'xl',
    children
}) {
    return (
        <Modal show={show} onHide={handleClose} size={size} centered>
            <Modal.Header closeButton style={{backgroundColor: "AEE9FF"}}>
                <Modal.Title>{title}</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {children}
            </Modal.Body>
            <Modal.Footer>
                <Button variant="outline-dark" onClick={handleClose}>
                    Закрыть
                </Button>
                {(primaryBtnText && handlePrimaryBtnClick) &&
                    <Button variant="success" onClick={handlePrimaryBtnClick} disabled={primaryBtnDisabled}>
                        {primaryBtnText}
                    </Button>}
            </Modal.Footer>
        </Modal>
    );
}
