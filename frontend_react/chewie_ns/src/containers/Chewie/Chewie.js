import React, { Component } from "react";
import { Link } from "react-router-dom";

// Assets imports
import INCDlogo from "../../assets/images/INCD-small.png";
import UMMIlogo from "../../assets/images/ummi1small2.png";
import IMMlogo from "../../assets/images/iMM_JLA_medium2.png";

// Material UI import
import SvgIcon from "@material-ui/core/SvgIcon";
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
          id="logoDiv" className={classes.logoDiv}
        >
          <div id="immLogoDiv">
            <img src={IMMlogo} alt="IMM" />
          </div>
          <div id="ummiLogoDiv" className={classes.ummiLogoDiv}>
            <img src={UMMIlogo} alt="UMMI!" />
          </div>
        </div>
        <div id="titleDIv" className={classes.titleDiv}>
          <h2>
            Chewie-NS Tutorial
          </h2>
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
            <img src={INCDlogo} alt="Resources provided by" />
          </div>
        </div>
      </div>
    );
  }
}

export default withErrorHandler(Chewie, axios);
