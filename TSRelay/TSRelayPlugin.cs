using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Drawing;
using System.Data;
using System.Text;
using System.Linq;
using System.Windows.Forms;
using Advanced_Combat_Tracker;
using System.IO;
using System.Reflection;
using System.Xml;
using TS3QueryLib.Core;
using TS3QueryLib.Core.Server;
using TS3QueryLib.Core.CommandHandling;
using TS3QueryLib.Core.Common.Responses;
using TS3QueryLib.Core.Server.Entities;


namespace ACT_Plugin
{
    public class TSRelayPlugin : UserControl, IActPluginV1
    {

        #region Plugin Constants (Fill in your own here)
        const ushort QUERY_PORT = 10011;
        const string LOGIN_ID = "admin";
        const string LOGIN_PASS = "r9serJRO";
        const string TS_HOST = "198.199.86.84";
        readonly string[] CHECKS = { "You cast Scathe", "You cast Flare" };
        #endregion


        #region Designer Created Code (Avoid editing)
        /// <summary> 
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary> 
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Component Designer generated code

        /// <summary> 
        /// Required method for Designer support - do not modify 
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {

        }

        #endregion
        #endregion


        private QueryRunner qr;
        private uint honeypot_cid;
        private uint bot_clid;


        public TSRelayPlugin()
        {
            InitializeComponent();
        }

        string settingsFile = Path.Combine(ActGlobals.oFormActMain.AppDataFolder.FullName, "Config\\TSRelay.config.xml");


        TreeNode optionsNode = null;

        #region IActPluginV1 Members
        public void InitPlugin(TabPage pluginScreenSpace, Label pluginStatusText)
        {
            // This is the GUI related stuff
            pluginScreenSpace.Controls.Add(this);
            this.Dock = DockStyle.Fill;

            int dcIndex = -1;   // Find the Data Correction node in the Options tab
            for (int i = 0; i < ActGlobals.oFormActMain.OptionsTreeView.Nodes.Count; i++)
            {
                if (ActGlobals.oFormActMain.OptionsTreeView.Nodes[i].Text == "Data Correction")
                    dcIndex = i;
            }
            if (dcIndex != -1)
            {
                // Add our own node to the Data Correction node
                optionsNode = ActGlobals.oFormActMain.OptionsTreeView.Nodes[dcIndex].Nodes.Add("EQ2 English Settings");
                // Register our user control(this) to our newly create node path.  All controls added to the list will be laid out left to right, top to bottom
                ActGlobals.oFormActMain.OptionsControlSets.Add(@"Data Correction\EQ2 English Settings", new List<Control> { this });
                Label lblConfig = new Label();
                lblConfig.AutoSize = true;
                lblConfig.Text = "Find the applicable options in the Options tab, Data Correction section.";
                pluginScreenSpace.Controls.Add(lblConfig);  // This is a placeholder label for when the UserControl is removed from the plugins tab and shown in the Options tab
            }


            // Register the log read event
            ActGlobals.oFormActMain.OnLogLineRead += new LogLineEventDelegate(oFormActMain_LogLineEvent);

            // Connect to the TS Server
            SyncTcpDispatcher dispatcher = new SyncTcpDispatcher(TS_HOST, QUERY_PORT);
            qr = new QueryRunner(dispatcher);
            dispatcher.Connect();

            // Select the default Virtual Server (1)
            qr.SelectVirtualServerById(1);

            // Log in as the bot
            qr.Login(LOGIN_ID, LOGIN_PASS);

            // Get our client ID (we don't know if this changes or not!)
            var response = qr.SendCommand(new Command("clientlist", new string[] { }));
            string[] entries = response.Split('|');
            foreach (string entry in entries)
            {
                if (entry.Contains("ParseBot") && entry.Contains("client_type=1"))
                {
                    int start = entry.IndexOf("clid=") + 5;
                    int end = entry.IndexOf(" ", start);
                    bot_clid = Convert.ToUInt32(entry.Substring(start, end - start));
                }
            }


            // Get our channel ID (we don't know if this changes or not!)
            response = qr.SendCommand(new Command("channellist", new string[] { }));
            entries = response.Split('|');
            foreach (string entry in entries)
            {
                if (entry.Contains("Bot\\sHoneypot"))
                {
                    int start = entry.IndexOf("cid=") + 4;
                    int end = entry.IndexOf(" ", start);
                    honeypot_cid = Convert.ToUInt32(entry.Substring(start, end - start));
                }
            }

            // Move to the honeypot channel
            qr.MoveClient(bot_clid, honeypot_cid);

            // Send a message to the honeypot channel
            qr.SendTextMessage(MessageTarget.Channel, honeypot_cid, "ParseBot is connected to the honeypot.");
        }


        public void DeInitPlugin()
        {
            // Unsubscribe from any events you listen to when exiting!
            ActGlobals.oFormActMain.AfterCombatAction -= oFormActMain_AfterCombatAction;
            ActGlobals.oFormActMain.OnLogLineRead -= oFormActMain_LogLineEvent;
        }
        #endregion


        /**
         * This is the callback for checking lines against custom events.
         **/
        void oFormActMain_LogLineEvent(bool isImport, LogLineEventArgs logInfo)
        {
            string entry = logInfo.logLine;
            foreach (string check in CHECKS)
            {
                if (entry.Contains(check))
                {
                    qr.SendTextMessage(MessageTarget.Channel, this.honeypot_cid, check);
                    break;
                }
            }

        }

        void oFormActMain_AfterCombatAction(bool isImport, CombatActionEventArgs actionInfo)
        {
            throw new NotImplementedException();
        }
    }
}
