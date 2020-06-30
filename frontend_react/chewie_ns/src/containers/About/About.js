import React, { Component } from "react";
import axios from "../../axios-backend";

// Chewie components imports
import text from "../../components/data/about_md";
import Markdown from "../../components/Markdown/Markdown";
import Copyright from "../../components/Copyright/Copyright";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import classes from "./About.module.css";

class About extends Component {
  render() {
    return (
      <div id="homeDiv" className={classes.homeDiv}>
        <Markdown markdown={text} />
        <Copyright />
      </div>
    );
  }
}

export default withErrorHandler(About, axios);