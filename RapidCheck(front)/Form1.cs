﻿using MaterialSkin;
using MaterialSkin.Controls;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.IO;
using System.Runtime.InteropServices;

//DirectX
using Microsoft.DirectX.AudioVideoPlayback;
using Microsoft.DirectX;
//MYSQL
using MySql.Data.MySqlClient;


namespace RapidCheck
{
    public partial class Form1 : MaterialForm
    {
        //DirectX
        private Video video;
        private Size formSize;
        private Size pnlSize;

        //Video File Path
        private string path;

        //MySQL
        private string strConn = "Server=localhost;Database=test;Uid=root;Pwd=1234;";

        public Form1()
        {
            InitializeComponent();
            var skinManager = MaterialSkinManager.Instance;
            skinManager.AddFormToManage(this);
            //skinManager.Theme = MaterialSkinManager.Themes.DARK;
            skinManager.Theme = MaterialSkinManager.Themes.LIGHT;
            skinManager.ColorScheme = new ColorScheme(Primary.BlueGrey800, Primary.BlueGrey900, Primary.BlueGrey500, Accent.LightBlue200, TextShade.WHITE);

            tabPage1.Text = "검색";
            tabPage2.Text = "요약";
            tabPage3.Text = "영상";

            //SQL
            MySqlConnection conn = new MySqlConnection(strConn);
            conn.Open();
            MySqlCommand cmd = new MySqlCommand("INSERT INTO test_table VALUES (11, 'tasdad1')", conn);
            cmd.ExecuteNonQuery();
            conn.Close();
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            formSize = new Size(this.Width, this.Height);
            pnlSize = new Size(tabPage3.Width, tabPage3.Height);
        }

        private void videoBtn_Click(object sender, EventArgs e)
        {
            MySqlConnection conn = new MySqlConnection(strConn);
            conn.Open();

            MySqlCommand cmd = new MySqlCommand("UPDATE test_table SET name='Tim' WHERE id=11");
            cmd.ExecuteNonQuery();

            conn.Close();
        }
        private void materialFlatButton2_Click(object sender, EventArgs e)
        {
            openFileDialog1.InitialDirectory = @"C:\Users\trevor\Desktop\Videos";
            if (openFileDialog1.ShowDialog() == DialogResult.OK)
            {
                // open the video
                // remember the original dimensions of the panel
                int height = videoPanel.Height;
                int width = videoPanel.Width;
                // dispose of the old video to clean up resources
                if (video != null)
                {
                    video.Dispose();
                }

                try
                {
                    // open a new video
                    video = new Video(openFileDialog1.FileName);
                    // assign the win form control that will contain the video
                    video.Owner = videoPanel;
                    // resize to fit in the panel
                    videoPanel.Width = width;
                    videoPanel.Height = height;
                    // play the first frame of the video so we can identify it
                    video.Play();
                    //video.Pause();
                }
                catch (Exception ex)
                {
                    materialFlatButton2.Text = "error";
                }
                
                
            }
            // enable video buttons
            //ControlLogic();
        }
    }
}
