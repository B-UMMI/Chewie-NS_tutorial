import React, { Component } from "react";
import { Link } from "react-router-dom";

// Assets imports
import INCDlogo from "../../assets/images/INCD-small.png";
import UMMIlogo from "../../assets/images/ummi1small2.png";
import IMMlogo from "../../assets/images/iMM_JLA_medium2.png";
import FMULlogo from "../../assets/images/fmul_logo.png";

// Material UI import
import Button from "@material-ui/core/Button";

// Chewie local imports
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import axios from "../../axios-backend";
import classes from "./Chewie.module.css";

class Chewie extends Component {
  render() {
    return (
      <div id="homeDiv" className={classes.homeDiv}>
        <div
          id="logoDiv"
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "center",
            marginTop: "-50px",
          }}
        >
          <a
            href={"https://imm.medicina.ulisboa.pt/"}
            target="_blank"
            rel="noopener noreferrer"
          >
            <img src={IMMlogo} alt="IMM" />
          </a>
          <a
            href={"https://www.medicina.ulisboa.pt/"}
            target="_blank"
            rel="noopener noreferrer"
          >
            <img src={FMULlogo} alt="FM" />
          </a>
          <a
            href={"http://im.fm.ul.pt"}
            target="_blank"
            rel="noopener noreferrer"
          >
            <img src={UMMIlogo} alt="UMMI!" />
          </a>
        </div>
        <div id="titleDIv" className={classes.titleDiv}>
          <h2>Chewie-NS Tutorial</h2>
        </div>
        <div id="bodyDiv" className={classes.bodyDiv}>
          <div style={{ marginTop: "30px" }}>
            <p>
              The objective of this tutorial site is to provide users with a
              sandbox-style service to try all the feautures Chewie-NS by
              allowing all users to submit and analyse the provided test
              schemas.
            </p>
            <p>
              For any issues or requests contact the development team at{" "}
              <a href="mailto:imm-bioinfo@medicina.ulisboa.pt">
                imm-bioinfo@medicina.ulisboa.pt
              </a>
              .
            </p>
          </div>
        </div>
        <div style={{ textAlign: "center", marginTop: "20px" }}>
          <div id="availableSchemasDiv" style={{ marginTop: "30px" }}>
            <Button
              variant="contained"
              color="default"
              component={Link}
              to="/stats"
            >
              Available Schemas
            </Button>
          </div>
        </div>
        <div id="INCD_div" className={classes.incdDiv}>
          <div id="resourcesTextDiv">
            <p className={classes.resourcesText}>
              <b>Resources provided by</b>
            </p>
            <a
              href={"https://www.incd.pt/"}
              target={"_blank"}
              rel={"noopener noreferrer"}
            >
              <img src={INCDlogo} alt="Resources provided by" />
            </a>
          </div>
        </div>
      </div>
    );
  }
}

export default withErrorHandler(Chewie, axios);
